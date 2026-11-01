#!/usr/bin/env python3
"""
Called by .github/workflows/fetch-linkedin.yml (weekly cron).

Reads CAN/TREE-2026Q3.json's connections{}, maps each to its fixed slug
(same table as .claude/skills/fetch-linkedin/SKILL.md — keep both in
sync if connections{} ever changes), and calls py-asis's listener
once per connection, sequentially with a pause between calls, prepending
each successful response as a new dated entry at the top of the single
MAY/LOG-2026Q3.log (one `## <fetchedAt> <SLUG>` entry per connection per run).

A failed/unreachable call for one connection is logged and skipped —
it never fails the whole job, and never touches that connection's
existing log. A missing log file is exactly what the fetch-linkedin
skill (STEP 1a) already treats as MISSING.

Quarter is hardcoded as 2026Q3 — update it at quarter rollover alongside
the rest of PIPE-2026Q3.yml's QUARTER ROLLOVER section.
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QUARTER = "2026Q3"
TREE_FILE = REPO_ROOT / "CAN" / f"TREE-{QUARTER}.json"
SECONDS_BETWEEN_CALLS = 30
REQUEST_TIMEOUT = 90
ANCHOR = "####### <!-- ANCHOR MARKER - ADD ALL NEW ENTRIES DIRECTLY BELOW THIS LINE -->"
LOG_PATH = REPO_ROOT / "MAY" / f"LOG-{QUARTER}.log"

# Must match .claude/skills/fetch-linkedin/SKILL.md's mapping table.
SLUG_MAP = {
    "ASIS New Zealand": "ASISNZ",
    "New Zealand Security Association (NZSA)": "NZSA",
    "ASIS International": "ASIS",
    "NZ Police": "NZPOLICE",
    "Johnson Controls": "JOHNSON",
    "Gallagher Security": "GALLAGHER",
    "Inner Range ANZ": "INNERRANGE",
    "Bosch Security and Safety Systems": "BOSCH",
    "Integrated Control Technology (ICT)": "ICT",
    "Jacques Technologies": "JACQUES",
}


def load_connections() -> list[tuple[str, str, str]]:
    """Returns [(slug, companyName, url), ...] from connections{}."""
    data = json.loads(TREE_FILE.read_text())
    connections = data.get("connections", {})
    out = []
    for group in ("own", "associations", "partners"):
        for name, entry in connections.get(group, {}).items():
            # entry is { "url": ..., "value": N } (a bare URL string is also accepted)
            url = entry["url"] if isinstance(entry, dict) else entry
            slug = SLUG_MAP.get(name)
            if not slug:
                print(f"WARNING: no slug mapping for connection {name!r} — "
                      f"skipping. Add it to SLUG_MAP and the fetch-linkedin "
                      f"skill's table.", file=sys.stderr)
                continue
            out.append((slug, name, url))
    return out


def fetch_one(base_url: str, slug: str, company_name: str, url: str,
              cf_client_id: str, cf_client_secret: str, shared_secret: str) -> bytes | None:
    qs = urllib.parse.urlencode({"slug": slug, "companyName": company_name, "url": url})
    full_url = f"{base_url}?{qs}"
    headers = {
        "User-Agent": "asis-linkedin-fetch/1.0 (+https://github.com/asisnz/md-asis)",
    }
    if cf_client_id and cf_client_secret:
        headers["CF-Access-Client-Id"] = cf_client_id
        headers["CF-Access-Client-Secret"] = cf_client_secret
    if shared_secret:
        headers["X-Listener-Secret"] = shared_secret

    req = urllib.request.Request(full_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            if resp.status != 200:
                print(f"slug={slug}: HTTP {resp.status} — skipping", file=sys.stderr)
                return None
            return resp.read()
    except urllib.error.HTTPError as exc:
        print(f"slug={slug}: HTTP {exc.code} — skipping", file=sys.stderr)
        return None
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"slug={slug}: request failed ({exc}) — skipping", file=sys.stderr)
        return None


def prepend_entry(log_path: Path, slug: str, data: dict) -> None:
    """Prepend a new ## <fetchedAt> <SLUG> / <compact JSON> entry to the log."""
    fetched_at = data.get("fetchedAt", "unknown")
    compact = json.dumps(data, separators=(",", ":"))
    new_entry = f"## {fetched_at} {slug}\n{compact}\n"

    if log_path.exists():
        text = log_path.read_text(encoding="utf-8")
        marker_pos = text.find(ANCHOR)
        if marker_pos == -1:
            # Malformed log — append at end as fallback
            log_path.write_text(text.rstrip() + f"\n\n{new_entry}", encoding="utf-8")
            return
        insert_at = marker_pos + len(ANCHOR)
        text = text[:insert_at] + f"\n\n{new_entry}" + text[insert_at:].lstrip("\n")
    else:
        text = f"FETCH LOG — {QUARTER}\n\n{ANCHOR}\n\n{new_entry}"

    log_path.write_text(text, encoding="utf-8")


def main() -> int:
    base_url = os.environ.get("LINKEDIN_FETCH_URL", "")
    if not base_url:
        print("LINKEDIN_FETCH_URL is not set — nothing to do", file=sys.stderr)
        return 1

    cf_client_id = os.environ.get("CF_ACCESS_CLIENT_ID", "")
    cf_client_secret = os.environ.get("CF_ACCESS_CLIENT_SECRET", "")
    shared_secret = os.environ.get("LISTENER_SHARED_SECRET", "")

    connections = load_connections()
    print(f"Fetching {len(connections)} connections, {SECONDS_BETWEEN_CALLS}s apart...")

    fetched, skipped = 0, 0
    for i, (slug, company_name, url) in enumerate(connections):
        body = fetch_one(base_url, slug, company_name, url,
                         cf_client_id, cf_client_secret, shared_secret)
        if body is None:
            skipped += 1
        else:
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                print(f"slug={slug}: non-JSON response — skipping", file=sys.stderr)
                skipped += 1
                continue
            prepend_entry(LOG_PATH, slug, parsed)
            fetched += 1
            print(f"slug={slug}: prepended entry to {LOG_PATH.relative_to(REPO_ROOT)}")

        if i < len(connections) - 1:
            time.sleep(SECONDS_BETWEEN_CALLS)

    print(f"Done: {fetched} written, {skipped} skipped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
