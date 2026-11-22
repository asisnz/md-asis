#!/usr/bin/env python3
"""
Called by .github/workflows/fetch-linkedin.yml (weekly cron).

Reads JSON/ASIS/JSON-2026Q4.json's connections{}, maps each to its fixed
slug, and calls py-asis's listener once per connection, appending each
successful response as a new JSON line to JSONL/ASIS/<SLUG>.jsonl.

One file per slug — oldest entry first (standard JSONL append order).
A failed/unreachable call for one connection is logged and skipped.
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
TREE_FILE = REPO_ROOT / "JSON" / "ASIS" / "JSON-2026Q4.json"
JSONL_DIR = REPO_ROOT / "JSONL" / "ASIS"
SECONDS_BETWEEN_CALLS = 30
REQUEST_TIMEOUT = 90

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


def append_entry(jsonl_dir: Path, slug: str, data: dict) -> None:
    """Append one JSON line to JSONL/ASIS/<slug>.jsonl."""
    jsonl_dir.mkdir(parents=True, exist_ok=True)
    path = jsonl_dir / f"{slug}.jsonl"
    compact = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    with open(path, "a", encoding="utf-8") as f:
        f.write(compact + "\n")


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
            append_entry(JSONL_DIR, slug, parsed)
            fetched += 1
            print(f"slug={slug}: appended entry to JSONL/ASIS/{slug}.jsonl")

        if i < len(connections) - 1:
            time.sleep(SECONDS_BETWEEN_CALLS)

    print(f"Done: {fetched} written, {skipped} skipped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
