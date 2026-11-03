#!/usr/bin/env python3
"""
Step 2D: Generate weekly media assets via Mac mini.

Reads the target week's posts with empty media URL from the CSV, sends them
to the Mac mini /generate-media endpoint (same tunnel + auth as gen_posts.py),
receives PNG/PDF/GIF files as base64, writes them to MAY/media/2026Q3/, and
updates the media URL column in the CSV.

No ANTHROPIC_API_KEY needed — the Mac mini uses its local Claude login.

Environment variables (supplied by the GitHub Action):
  GENERATE_CONTENT_URL    — base Cloudflare Tunnel URL (same as gen_posts.py)
  CF_ACCESS_CLIENT_ID     — Cloudflare Access service token ID
  CF_ACCESS_CLIENT_SECRET — Cloudflare Access service token secret
  LISTENER_SHARED_SECRET  — shared secret verified by listener.py
  CONTENT_WEEK            — optional ISO week override (default: current week)
"""

import base64
import csv
import io
import json
import os
import time
import requests
from datetime import date
from pathlib import Path

QUARTER    = "2026Q3"
TABLE_PATH = f"COULD/TABLE-{QUARTER}.csv"
MEDIA_DIR  = Path(f"MAY/media/{QUARTER}")
SKILL_PATH = Path(".claude/skills/generate-media/SKILL.md")
LOGO_PATH  = Path("logo.svg")
LOGO_MIME  = "image/svg+xml"
PAGES_BASE = f"https://asisnz.github.io/md-asis/MAY/media/{QUARTER}"

GENERATABLE = {"png", "gif", "pdf"}


def week_num() -> int:
    env = os.environ.get("CONTENT_WEEK", "")
    return int(env) if env else date.today().isocalendar()[1]


def load_csv() -> tuple[list[str], list[dict]]:
    with open(TABLE_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = [h.strip() for h in reader.fieldnames]
        rows = [{(k or "").strip(): v for k, v in r.items()} for r in reader]
    return fieldnames, rows


def load_system_prompt() -> str:
    text = SKILL_PATH.read_text(encoding="utf-8")
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    return text.strip()



def _cf_headers() -> dict:
    """CF Access + listener auth headers for every Mac mini call."""
    return {
        "CF-Access-Client-Id":     os.environ.get("CF_ACCESS_CLIENT_ID", ""),
        "CF-Access-Client-Secret": os.environ.get("CF_ACCESS_CLIENT_SECRET", ""),
        "X-Listener-Secret":       os.environ["LISTENER_SHARED_SECRET"],
    }


def call_mac_mini_one(post: dict, system_prompt: str, logob64: str, week: int,
                      logomime: str = "image/jpeg") -> list[dict]:
    """POST /generate-media for one post (returns job_id immediately — async),
    then poll /generate-media-status/<job_id> until done or deadline."""
    base_url = os.environ["GENERATE_CONTENT_URL"].rstrip("/")
    headers  = {**_cf_headers(), "Content-Type": "application/json"}
    payload  = {
        "systemPrompt": system_prompt,
        "logob64":      logob64,
        "logomime":     logomime,
        "week":         week,
        "posts":        [post],
    }
    print(f"  {post['item']} → {base_url}/generate-media …")
    resp = requests.post(base_url + "/generate-media", headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        print(f"  {post['item']} error: {data['error']}")
        return []

    job_id     = data["job_id"]
    status_url = f"{base_url}/generate-media-status/{job_id}"
    poll_hdrs  = _cf_headers()
    # pdf=5 claude calls, gif=3 — each up to 450s; add 300s headroom
    mtype    = post.get("media-type", "png").lower()
    max_calls = 5 if mtype == "pdf" else (3 if mtype == "gif" else 1)
    deadline  = time.time() + (max_calls * 450) + 300

    print(f"  {post['item']} job {job_id} — polling (deadline {max_calls*450+300}s) …")
    while time.time() < deadline:
        time.sleep(15)
        r = requests.get(status_url, headers=poll_hdrs, timeout=30)
        if r.status_code == 404:
            print(f"  {post['item']} job lost (listener restarted?) — skipping")
            return []
        r.raise_for_status()
        state = r.json()
        if state["status"] == "done":
            files = state.get("files", [])
            print(f"  {post['item']} done ({len(files)} file(s))")
            return files
        if state["status"] == "error":
            print(f"  {post['item']} Mac mini error: {state.get('error', 'unknown')}")
            return []
        print(f"  {post['item']} pending …")

    print(f"  {post['item']} timed out")
    return []


def main() -> None:
    week = week_num()
    fieldnames, rows = load_csv()

    targets = [
        r for r in rows
        if r.get("week") == str(week)
        and not r.get("media URL", "").strip()
        and r.get("media-type", "").strip().lower() in GENERATABLE
    ]

    skipped = [
        r for r in rows
        if r.get("week") == str(week)
        and not r.get("media URL", "").strip()
        and r.get("media-type", "").strip().lower() not in GENERATABLE
    ]

    if skipped:
        for r in skipped:
            print(f"  skip {r['item']} ({r['media-type']}) — requires real asset")

    if not targets:
        print(f"No generatable posts with empty media URL for week {week}.")
        return

    print(f"Generating media for {len(targets)} post(s) (week {week}) — one call per post:")
    for t in targets:
        print(f"  {t['item']} | {t['media-type']} | {t['media'][:60]}")

    system_prompt = load_system_prompt()
    logob64       = base64.b64encode(LOGO_PATH.read_bytes()).decode()
    logomime      = LOGO_MIME

    all_files: list[dict] = []
    for post in targets:
        files = call_mac_mini_one(post, system_prompt, logob64, week, logomime)
        all_files.extend(files)

    if not all_files:
        print("No files returned from Mac mini.")
        return

    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    url_map: dict[str, str] = {}
    for f in all_files:
        out = MEDIA_DIR / Path(f["path"]).name
        out.write_bytes(base64.b64decode(f["content_b64"]))
        print(f"  wrote {out} ({out.stat().st_size // 1024} KB)")
        item = f["item"]
        url  = f"{PAGES_BASE}/{out.name}"
        if item not in url_map or out.suffix in (".pdf", ".gif"):
            url_map[item] = url

    for row in rows:
        if row.get("item") in url_map:
            row["media URL"] = url_map[row["item"]]

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows(rows)
    with open(TABLE_PATH, "w", newline="", encoding="utf-8") as f:
        f.write(buf.getvalue())

    print(f"Updated {len(url_map)} media URL(s) in {TABLE_PATH}.")


if __name__ == "__main__":
    main()
