#!/usr/bin/env python3
"""
Step 2: Generate weekly content batch.

Builds a payload from local repo files (TREE JSON + MAY logs + TABLE CSV),
POSTs it to the Mac mini listener via Cloudflare Tunnel, receives a JSON
array of 6 generated posts, validates them, then appends to TABLE CSV.

The Mac mini listener handles the Claude API call — no Anthropic key needed
in GitHub secrets.

Environment variables (supplied by the GitHub Action):
  GENERATE_CONTENT_URL    — Cloudflare Tunnel URL for the /generate-content endpoint
  CF_ACCESS_CLIENT_ID     — Cloudflare Access service token ID
  CF_ACCESS_CLIENT_SECRET — Cloudflare Access service token secret
  LISTENER_SHARED_SECRET  — shared secret verified by listener.py
  CONTENT_WEEK            — optional ISO week override (default: current week)
"""

import csv
import io
import json
import os
import re
import requests
from datetime import date, timedelta
from pathlib import Path

QUARTER      = "2026Q3"
TABLE_PATH   = f"COULD/TABLE-{QUARTER}.csv"
TREE_PATH    = f"CAN/TREE-{QUARTER}.json"
LOG_DIR      = Path("MAY")
SKILL_PATH   = Path(".claude/skills/generate-post/SKILL.md")
FETCH_ANCHOR = "####### <!-- ANCHOR MARKER - ADD ALL NEW ENTRIES DIRECTLY BELOW THIS LINE -->"

SLUG_ORDER = [
    "ASISNZ", "NZSA", "ASIS", "NZPOLICE",
    "JOHNSON", "GALLAGHER", "INNERRANGE", "BOSCH", "ICT", "JACQUES",
]

PILLARS = ["SERVICES", "INDUSTRY", "AUTHORITY", "PEOPLE", "TRUST", "ENGAGEMENT"]


# ── helpers ──────────────────────────────────────────────────────────────────

def week_num() -> int:
    env = os.environ.get("CONTENT_WEEK", "")
    return int(env) if env else date.today().isocalendar()[1]


def parse_latest_log_entry(slug: str) -> dict | None:
    """Newest entry for this connection in the single fetch log (newest first)."""
    log = LOG_DIR / f"LOG-{QUARTER}.log"
    if not log.exists():
        return None
    text = log.read_text(encoding="utf-8")
    anchor_pos = text.find(FETCH_ANCHOR)
    if anchor_pos == -1:
        return None
    after = text[anchor_pos + len(FETCH_ANCHOR):]
    for m in re.finditer(r"## \S+ (\S+)\n(\{[^\n]+\})", after):
        if m.group(1) != slug:
            continue
        try:
            return json.loads(m.group(2))
        except json.JSONDecodeError:
            return None
    return None


def load_connections(window_start: date, window_end: date) -> list[dict]:
    connections = []
    for slug in SLUG_ORDER:
        data = parse_latest_log_entry(slug)
        if not data:
            continue
        recent = [
            p for p in data.get("recentPosts", [])
            if window_start <= date.fromisoformat(p["date"]) <= window_end
        ]
        connections.append({
            "slug": slug,
            "companyName": data.get("companyName", slug),
            "url": data.get("url", ""),
            "bio": data.get("bio", ""),
            "fetchedAt": data.get("fetchedAt", ""),
            "recentPosts": recent,
        })
    return connections


def load_csv() -> tuple[list[str], list[dict]]:
    with open(TABLE_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # The committed header's last column has been read back as
        # "sources\r\r" (stray CRs inside the quotes), which made
        # append_posts' "sources" key fail DictWriter. Strip header names so
        # the rewrite below also repairs the header.
        fieldnames = [h.strip() for h in reader.fieldnames]
        rows = [{(k or "").strip(): v for k, v in r.items()} for r in reader]
    return fieldnames, rows


def used_subtypes(rows: list[dict]) -> list[dict]:
    return [
        {"topic": r["topic"], "type": r["type"], "subtopic": r["subtopic"]}
        for r in rows
        if r.get("topic") and r.get("type") and r.get("subtopic")
    ]


def next_item_num(rows: list[dict]) -> int:
    nums = [
        int(r["item"].replace("post-", ""))
        for r in rows
        if re.fullmatch(r"post-\d+", r.get("item", ""))
    ]
    return (max(nums) if nums else 0) + 1


def load_system_prompt() -> str:
    """SKILL.md body (frontmatter stripped), sent to the listener so the Mac
    mini never needs a git pull to stay current."""
    text = SKILL_PATH.read_text(encoding="utf-8")
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    return text.strip()


def build_payload(week: int, rows: list[dict], tree: dict) -> dict:
    today = date.today()
    window_start = today - timedelta(days=7)
    return {
        "systemPrompt": load_system_prompt(),
        "quarter": QUARTER,
        "week": week,
        "today": str(today),
        "window": f"{window_start} to {today}",
        "nextItemStart": next_item_num(rows),
        "usedSubtypes": used_subtypes(rows),
        "tree": tree,
        "connections": load_connections(window_start, today),
    }


# ── Mac mini call ─────────────────────────────────────────────────────────────

def call_mac_mini(payload: dict) -> list[dict]:
    url     = os.environ["GENERATE_CONTENT_URL"].rstrip("/") + "/generate-content"
    headers = {
        "CF-Access-Client-Id":     os.environ["CF_ACCESS_CLIENT_ID"],
        "CF-Access-Client-Secret": os.environ["CF_ACCESS_CLIENT_SECRET"],
        "X-Listener-Secret":       os.environ["LISTENER_SHARED_SECRET"],
        "Content-Type":            "application/json",
    }
    print(f"Calling Mac mini at {url} …")
    resp = requests.post(url, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()
    data = resp.json()
    # Listener may return {"posts": [...]} or a bare array
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "posts" in data:
        return data["posts"]
    raise ValueError(f"Unexpected response shape: {str(data)[:200]}")


# ── validation ────────────────────────────────────────────────────────────────

DOUBLE_HYPHEN = re.compile(r"--")

def validate_posts(posts: list[dict]) -> None:
    if len(posts) != 6:
        raise ValueError(f"Expected 6 posts, got {len(posts)}")
    topics = sorted(p.get("topic", "") for p in posts)
    if topics != sorted(PILLARS):
        raise ValueError(f"Posts must cover all 6 pillars. Got: {topics}")
    for p in posts:
        for field in ("title", "description"):
            val = p.get(field, "")
            if DOUBLE_HYPHEN.search(val):
                raise ValueError(
                    f"Double hyphen in {p.get('topic')} / {field}: {val[:80]}"
                )


# ── CSV write ─────────────────────────────────────────────────────────────────

def serialize_csv(rows: list[dict], fieldnames: list[str]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def append_posts(
    posts: list[dict],
    existing_rows: list[dict],
    fieldnames: list[str],
    week: int,
) -> list[dict]:
    today = str(date.today())
    item_num = next_item_num(existing_rows)
    new_rows = []
    for post in posts:
        row = {h: "" for h in fieldnames}
        row.update({
            "week": str(week),
            "item": f"post-{item_num:03d}",
            "topic": post.get("topic", ""),
            "type": post.get("type", ""),
            "subtopic": post.get("subtopic", ""),
            "title": post.get("title", ""),
            "description": post.get("description", ""),
            "media": post.get("media", ""),
            "media-type": post.get("media-type", ""),
            "media URL": "",
            "linkedin account tag": post.get("linkedin account tag", ""),
            "hashtag": post.get("hashtag", ""),
            "score": str(post.get("score", "")),
            "createdat": today,
            "updatedat": today,
            "feedback": "",
            "feedback-comment": "",
            "sources": post.get("sources", ""),
        })
        new_rows.append(row)
        item_num += 1
    return new_rows


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    week = week_num()
    fieldnames, existing_rows = load_csv()
    if os.environ.get("CONTENT_REPLACE") == "true":
        # Redo a batch: drop that week's rows first so the new posts reuse
        # the same item numbers and their subtypes count as unused again.
        kept = [r for r in existing_rows if r.get("week") != str(week)]
        print(f"Replacing week {week}: dropping {len(existing_rows) - len(kept)} existing rows")
        existing_rows = kept
    tree = json.loads(Path(TREE_PATH).read_text(encoding="utf-8"))

    payload = build_payload(week, existing_rows, tree)
    posts   = call_mac_mini(payload)

    validate_posts(posts)

    new_rows = append_posts(posts, existing_rows, fieldnames, week)
    all_rows = existing_rows + new_rows

    with open(TABLE_PATH, "w", newline="", encoding="utf-8") as f:
        f.write(serialize_csv(all_rows, fieldnames))

    print(f"Added {len(new_rows)} posts for week {week}:")
    for r in new_rows:
        print(f"  {r['item']} | {r['topic']} / {r['type']} / {r['subtopic']}")


if __name__ == "__main__":
    main()
