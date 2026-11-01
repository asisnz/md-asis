#!/usr/bin/env python3
"""Generate a PR body for the weekly content batch.

Reads the key files and assembles the PR description in
CAN → COULD → MAY → MIGHT section order.

Usage:
    python3 .github/scripts/gen_pr_body.py <week_number>

Example:
    python3 .github/scripts/gen_pr_body.py 44 > /tmp/pr_body.md
    gh pr create --title "content(w44): ..." --body-file /tmp/pr_body.md
"""

import csv
import json
import re
import subprocess
import sys
import yaml
from datetime import date, timedelta
from pathlib import Path

QUARTER = "2026Q3"
TABLE   = f"COULD/TABLE-{QUARTER}.csv"
ASSET   = f"MIGHT/ASSET-{QUARTER}.md"
PIPE    = f"PIPE-{QUARTER}.yml"

FETCH_ANCHOR = "####### <!-- ANCHOR MARKER - ADD ALL NEW ENTRIES DIRECTLY BELOW THIS LINE -->"

SLUG_ORDER = [
    "ASISNZ", "NZSA", "ASIS", "NZPOLICE",
    "JOHNSON", "GALLAGHER", "INNERRANGE", "BOSCH", "ICT", "JACQUES",
]


def pipe_mermaid() -> str:
    with open(PIPE, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    meta = data.get("meta", {})
    root_label = f"{meta.get('name', PIPE)} · {meta.get('quarter', QUARTER)}"
    lines = ["```mermaid", "graph LR", f'  ROOT(["{root_label}"])']
    for step in data.get("steps", []):
        sid = step["id"].replace("-", "_").upper()
        lines.append(f'  ROOT --> {sid}["{step["id"]} · {step["name"]}"]')
        for sub in step.get("substeps", []):
            subid = f'{sid}_{sub["id"].replace("-", "_").upper()}'
            lines.append(f'  {sid} --> {subid}("{sub["id"]} · {sub["name"]}")')
    lines.append("```")
    return "\n".join(lines)


def mermaid_block() -> str:
    return subprocess.check_output(
        ["python3", ".github/scripts/gen_tree_mermaid.py"], text=True
    ).strip()


def _parse_latest_entry(slug: str) -> dict | None:
    """Newest entry for this connection in the single fetch log (newest first)."""
    log_path = Path(f"MAY/LOG-{QUARTER}.log")
    if not log_path.exists():
        return None
    text = log_path.read_text(encoding="utf-8")
    after = text[text.find(FETCH_ANCHOR) + len(FETCH_ANCHOR):]
    for m in re.finditer(r"## \S+ (\S+)\n(\{[^\n]+\})", after):
        if m.group(1) != slug:
            continue
        try:
            return json.loads(m.group(2))
        except json.JSONDecodeError:
            return None
    return None


def connection_activity(week: int) -> str:
    """Return posts from MAY/LOG-*.log within the last 7 days (rolling window).

    Anchored to today so the section is fairly labelled as this week's signals
    regardless of where the ISO week boundary falls.
    """
    end   = date.today()
    start = end - timedelta(days=7)

    blocks = []
    for slug in SLUG_ORDER:
        data = _parse_latest_entry(slug)
        if not data:
            continue
        week_posts = [
            p for p in data.get("recentPosts", [])
            if start <= date.fromisoformat(p["date"]) <= end
        ]
        if not week_posts:
            continue
        company = data.get("companyName", slug)
        lines = [f"**{company}**"]
        for p in week_posts:
            snippet = p["text"][:120].replace("\n", " ")
            if len(p["text"]) > 120:
                snippet += "…"
            lines.append(f"- {p['date']}: {snippet}")
        blocks.append("\n".join(lines))

    if not blocks:
        return f"_No connection posts in the last 7 days ({start} – {end})._"
    return "\n\n".join(blocks)


def posts_table(week: int) -> str:
    with open(TABLE, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if int(r["week"]) == week]
    if not rows:
        return f"_No posts found for week {week}._"
    lines = [
        "| Post | Pillar | Subtype | Score | Media |",
        "|------|--------|---------|-------|-------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['item']} | {r['topic']} | {r['type']} / {r['subtopic']}"
            f" | {r['score']} | {r['media-type']} |"
        )
    return "\n".join(lines)


def asset_entry() -> str:
    """Return the most recent ASSET entry (between anchor and next ##)."""
    text = open(ASSET, encoding="utf-8").read()
    anchor = "<!-- ANCHOR MARKER - ADD ALL NEW ASSET ENTRIES DIRECTLY BELOW THIS LINE -->"
    after = text[text.find(anchor) + len(anchor):]
    m = re.search(r"(## ASSET:.*?)(?=\n## ASSET:|\Z)", after, re.DOTALL)
    return m.group(1).strip() if m else "_No asset entry found._"


def pipeline_para() -> str:
    with open(PIPE, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    steps = data.get("steps", [])
    step_names = [f"**{s['id']} ({s['name']})**" for s in steps]
    total_subs = sum(len(s.get("substeps", [])) for s in steps)
    parts = [
        f"The pipeline orchestrates the {data.get('meta', {}).get('name', 'automation')} workflow "
        f"across {len(steps)} steps — {' and '.join(step_names)} — with {total_subs} substeps in total. "
        f"It is the single source of truth for how the workflow runs: what triggers it, what it reads, "
        f"what it writes, and in what order."
    ]
    for s in steps:
        subs = s.get("substeps", [])
        if not subs:
            continue
        sub_list = ", ".join(f"`{sub['id']} {sub['name']}`" for sub in subs)
        trigger = s.get("trigger", "").split("—")[0].strip() or "manual"
        parts.append(
            f"{s['id'].capitalize()} ({s['name']}) runs {len(subs)} substeps: {sub_list}. "
            f"Trigger: {trigger}."
        )
    return "\n\n".join(parts)


def tree_para() -> str:
    with open(f"CAN/TREE-{QUARTER}.json", encoding="utf-8") as f:
        data = json.load(f)
    conns = data.get("connections", {})
    own = list(conns.get("own", {}).keys())
    assoc = list(conns.get("associations", {}).keys())
    partners = list(conns.get("partners", {}).keys())
    tree = data.get("tree", [])
    pillars = [t["category"] for t in tree]
    won = [
        name
        for group in conns.values()
        for name, meta in group.items()
        if isinstance(meta, dict) and meta.get("value", 0) > 0
    ]
    parts = [
        f"The content strategy tree maps the full universe of topics available to "
        f"{own[0] if own else 'the company'} across {len(pillars)} pillars: "
        f"{', '.join(pillars)}. "
        f"Each pillar branches into subtypes that generate post angles — the tree grows as new "
        f"subtypes are validated and locked in."
    ]
    all_conns = assoc + partners
    if all_conns:
        parts.append(
            f"The tree also tracks {len(all_conns)} monitored LinkedIn connections across associations "
            f"({', '.join(assoc)}) and partners ({', '.join(partners)}). "
            + (
                f"Connections with value > 0 this quarter: {', '.join(won)}."
                if won else
                "No connections have accrued value this quarter yet."
            )
        )
    return "\n\n".join(parts)


def posts_para(week: int) -> str:
    with open(TABLE, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if int(r["week"]) == week]
    if not rows:
        return f"No posts were generated for week {week}."
    pillars = list(dict.fromkeys(r["topic"] for r in rows))
    scored = sorted(rows, key=lambda r: int(r.get("score", 0)), reverse=True)
    top = scored[0] if scored else None
    parts = [
        f"Week {week} produced {len(rows)} post{'s' if len(rows) != 1 else ''} "
        f"spanning {len(pillars)} pillar{'s' if len(pillars) != 1 else ''}: "
        f"{', '.join(pillars)}. "
        f"Each post is scored for engagement potential — higher scores reflect stronger "
        f"relevance to current industry signals picked up in the connection feed."
    ]
    if top:
        parts.append(
            f"Highest-scoring post this week: **{top['item']}** "
            f"({top['topic']} / {top['subtopic']}, score {top['score']}) — "
            f"media type: {top.get('media-type', 'none')}."
        )
    return "\n\n".join(parts)


def activity_para(week: int) -> str:
    end   = date.today()
    start = end - timedelta(days=7)
    active = []
    for slug in SLUG_ORDER:
        d = _parse_latest_entry(slug)
        if not d:
            continue
        week_posts = [
            p for p in d.get("recentPosts", [])
            if start <= date.fromisoformat(p["date"]) <= end
        ]
        if week_posts:
            active.append((d.get("companyName", slug), len(week_posts)))
    if not active:
        return f"No connection activity was recorded in the last 7 days ({start} – {end})."
    total_posts = sum(c for _, c in active)
    names = ", ".join(f"**{name}** ({count})" for name, count in active)
    parts = [
        f"{len(active)} of {len(SLUG_ORDER)} monitored connections posted in the last 7 days "
        f"({start} – {end}), generating {total_posts} signal{'s' if total_posts != 1 else ''} in total. "
        f"Active connections: {names}."
    ]
    parts.append(
        "These posts feed the content strategy — topics surfacing repeatedly across connections "
        "or associations are candidates for the next batch's angle selection."
    )
    return "\n\n".join(parts)


def asset_para() -> str:
    text = open(ASSET, encoding="utf-8").read()
    anchor = "<!-- ANCHOR MARKER - ADD ALL NEW ASSET ENTRIES DIRECTLY BELOW THIS LINE -->"
    after = text[text.find(anchor) + len(anchor):]
    entries = re.findall(r"## ASSET:.*?(?=\n## ASSET:|\Z)", after, re.DOTALL)
    count = len(entries)
    parts = [
        f"The asset log tracks all verified decisions, completed runs, and open blockers for "
        f"{QUARTER}. It holds {count} entr{'ies' if count != 1 else 'y'} to date — "
        f"each entry is permanent and append-only, providing a full audit trail of what changed "
        f"and why."
    ]
    if entries:
        latest = entries[0].strip()
        title_match = re.match(r"## ASSET:\S+ (\S+) -> (.+)", latest)
        if title_match:
            parts.append(
                f"Most recent entry ({title_match.group(1)}): {title_match.group(2).strip()}."
            )
    return "\n\n".join(parts)


def gen_pr_body(week: int) -> str:
    return f"""\
## Pipeline (`PIPE-{QUARTER}.yml`)

{pipeline_para()}

{pipe_mermaid()}

## Content Strategy Tree (`CAN/TREE-{QUARTER}.json`)

{tree_para()}

> Auto-updated whenever the tree JSON changes on main — suggest changes by commenting below.

<!-- TREE-START -->
{mermaid_block()}
<!-- TREE-END -->

## Posts (`COULD/TABLE-{QUARTER}.csv`)

{posts_para(week)}

{posts_table(week)}

## Connection activity (`MAY/`)

{activity_para(week)}

{connection_activity(week)}

## Assets (`MIGHT/ASSET-{QUARTER}.md`)

{asset_para()}

{asset_entry()}
"""


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <week_number>", file=sys.stderr)
        sys.exit(1)
    print(gen_pr_body(int(sys.argv[1])), end="")
