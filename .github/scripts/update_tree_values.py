#!/usr/bin/env python3
"""
Step 1b: write reviewer-feedback "value" onto CAN/TREE-<quarter>.json.

One rule, applied to both sides of every rated post:
    value = wins - losses   (win +1, tie 0, lost -1)

  - subtypes: each rated post credits the subtype named by its
    topic / type / subtopic (== tree category / type / subtype name).
    Written as "value" on the one-line subtype objects.
  - connections: each rated post credits every connection named in its
    free-text "sources" column (by company page URL, or by name as a fallback);
    the "linkedin account tag" column is deliberately not used
    (own / associations / partners). Each entry in
    connections{} is { "url": ..., "value": N }.

Counts come from COULD/TABLE-<quarter>.csv. Unrated posts count for nothing.

The tree is hand-edited, so only the subtype lines and the connections{} entry
lines are rewritten; every other byte is left alone. Idempotent. A stale
"rated" field, or a "connectionsValue" / "connectionsUsed" block from earlier
versions, is removed.
Feedback rows that match no subtype are printed to stderr (a renamed subtype
would otherwise silently lose its value).

Usage:  python3 .github/scripts/update_tree_values.py
"""

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

QUARTER = "2026Q3"
ROOT = Path(__file__).resolve().parents[2]
TREE_PATH = ROOT / "CAN" / f"TREE-{QUARTER}.json"
TABLE_PATH = ROOT / "COULD" / f"TABLE-{QUARTER}.csv"

SCORES = {"win": 1, "tie": 0, "lost": -1}
GROUPS = ("own", "associations", "partners")
RETIRED_BLOCKS = ('  "connectionsValue"', '  "connectionsUsed"')

# Extra spellings the generator may use in "sources" for each connection
# (its full name, and any parenthetical in it, are always matched too).
# Keep in sync with connections{} when one is added.
ALIASES = {
    "ASIS New Zealand": ["ASIS New Zealand", "ASISNZ"],
    "New Zealand Security Association (NZSA)": ["NZSA"],
    "NZ Police": ["New Zealand Police"],
    "Johnson Controls": ["Johnson"],
    "Gallagher Security": ["Gallagher"],
    "Inner Range ANZ": ["Inner Range"],
    "Bosch Security and Safety Systems": ["Bosch"],
    "Integrated Control Technology (ICT)": ["ICT"],
    "Jacques Technologies": ["Jacques"],
}
CATEGORY_RE = re.compile(r'^\s*"category":\s*(".*"),?\s*$')
TYPE_RE = re.compile(r'^\s*"type":\s*(".*"),?\s*$')
SUBTYPE_RE = re.compile(r'^(\s*)(\{.*\})(,?)\s*$')
CONN_RE = re.compile(r'^(\s+)("(?:[^"\\]|\\.)*"):\s*(.+?)(,?)\s*$')


def load_rated_rows() -> list:
    """Rows with a win/tie/lost verdict: [(score, topic, type, subtopic, cited text)]."""
    rows = []
    with open(TABLE_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row = {(k or "").strip(): v for k, v in row.items()}
            verdict = (row.get("feedback") or "").strip().lower()
            if verdict in SCORES:
                # Connections are credited from "sources" only (company page
                # URLs; names as a fallback). The tag column is ignored: the own
                # page is tagged on every post and tags are sometimes added
                # for reach, not because the connection informed the post.
                cited = row.get("sources") or ""
                rows.append((SCORES[verdict], row["topic"], row["type"],
                             row["subtopic"], cited))
    return rows


COMPANY_URL_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/company/([^/?#\s;,]+)\S*", re.I)


def company_slug(url: str):
    """Company slug from a LinkedIn company page URL (scheme, www., trailing
    /home/ or /posts/ ignored), or None."""
    m = COMPANY_URL_RE.search(url or "")
    return m.group(1).lower() if m else None


def alias_patterns(name: str) -> list:
    spellings = {re.sub(r"\s*\(.*?\)", "", name).strip(), name, *ALIASES.get(name, [])}
    spellings.update(re.findall(r"\(([^)]+)\)", name))
    return [re.compile(rf"(?<!\w){re.escape(x)}(?!\w)", re.I) for x in spellings if x]


def connection_values(connections: dict, rated: list) -> dict:
    # Per post: the company slugs cited as URLs, and the remaining text (URLs
    # stripped, so a short name can't match inside someone else's URL).
    cited = []
    for score, _, _, _, text in rated:
        slugs = {m.group(1).lower() for m in COMPANY_URL_RE.finditer(text)}
        cited.append((score, slugs, COMPANY_URL_RE.sub(" ", text)))

    values = {}
    for group in GROUPS:
        values[group] = {}
        for name, entry in connections.get(group, {}).items():
            slug = company_slug(entry.get("url") if isinstance(entry, dict) else entry)
            pats = alias_patterns(name)
            values[group][name] = sum(
                score for score, slugs, plain in cited
                if (slug and slug in slugs) or any(p.search(plain) for p in pats)
            )
    return values


def drop_retired_blocks(lines: list) -> list:
    """Remove the earlier sibling connectionsValue / connectionsUsed block."""
    while True:
        start = next((i for i, l in enumerate(lines) if l.startswith(RETIRED_BLOCKS)), None)
        if start is None:
            return lines
        end = next(j for j in range(start, len(lines)) if lines[j] == "  },")
        lines = lines[:start] + lines[end + 1:]


def main() -> None:
    rated = load_rated_rows()
    subtype_values = defaultdict(int)
    for score, topic, type_, subtopic, _ in rated:
        subtype_values[(topic, type_, subtopic)] += score

    connections = json.loads(TREE_PATH.read_text(encoding="utf-8")).get("connections", {})
    conn_values = connection_values(connections, rated)

    seen = set()
    category = type_ = None
    in_conn = False
    out = []
    for line in TREE_PATH.read_text(encoding="utf-8").split("\n"):
        if line.startswith('  "connections": {'):
            in_conn = True
        elif in_conn and line == "  },":
            in_conn = False
        elif in_conn and (m := CONN_RE.match(line)) and not m.group(3).endswith("{"):
            name = json.loads(m.group(2))
            raw = json.loads(m.group(3)) if not m.group(3).startswith("{") else json.loads(m.group(3))
            url = raw["url"] if isinstance(raw, dict) else raw
            group_values = next((g for g in conn_values.values() if name in g), {})
            line = (f'{m.group(1)}{json.dumps(name, ensure_ascii=False)}: '
                    f'{{ "url": {json.dumps(url)}, "value": {group_values.get(name, 0)} }}{m.group(4)}')
        elif m := CATEGORY_RE.match(line):
            category = json.loads(m.group(1))
        elif m := TYPE_RE.match(line):
            type_ = json.loads(m.group(1))
        elif (m := SUBTYPE_RE.match(line)) and '"name"' in line:
            sub = json.loads(m.group(2))
            key = (category, type_, sub["name"])
            seen.add(key)
            sub.pop("rated", None)
            sub["value"] = subtype_values.get(key, 0)
            body = ", ".join(
                f"{json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}"
                for k, v in sub.items()
            )
            line = f"{m.group(1)}{{ {body} }}{m.group(3)}"
        out.append(line)

    for key in subtype_values:
        if key not in seen:
            print(f"WARNING: feedback for {key} matches no tree subtype", file=sys.stderr)

    new = "\n".join(drop_retired_blocks(out))
    if new != TREE_PATH.read_text(encoding="utf-8"):
        TREE_PATH.write_text(new, encoding="utf-8")
        print("Tree values updated.")
    else:
        print("Tree values already current.")


if __name__ == "__main__":
    main()
