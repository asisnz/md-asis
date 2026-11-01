---
name: fetch-linkedin
description: Use during STEP 1a (RESEARCH / fetch()) of a ASIS New Zealand content batch. Reads the cached per-connection LinkedIn snapshots in the single MAY/LOG-<quarter>.log — written weekly by the fetch-linkedin GitHub Action — instead of calling LinkedIn directly, which blocks unauthenticated fetch(). Summarizes recent partner/association activity to inform STEP 1b subtype selection.
---

# fetch-linkedin

Implements STEP 1a from the root `README.md` using the cached-snapshot design
recorded in `MIGHT/ASSET-<quarter>.md` ("Claude skill plan: LinkedIn fetch via
macnimi server + GitHub Action", Option B). A separate GitHub Action
(`.github/workflows/fetch-linkedin.yml`, not yet built) calls an authenticated
macnimi/Puppeteer server on a weekly cron and commits one JSON snapshot per
connection into `CAN/`. This skill only **reads** those snapshots — it never
calls LinkedIn itself and never writes cache files.

## When to use this

Any time an agent is running STEP 1 of the orchestration and reaches 1a. It
replaces the old instruction to `fetch()` each LinkedIn page URL directly.

## Steps

1. **Load the connection list.**
   Read `CAN/TREE-<quarter>.json` (e.g. `CAN/TREE-2026Q3.json`) and pull
   `connections{}` — `own`, `associations`, `partners`. Each entry is `{ "url": ..., "value": N }`; use `url` (`value` is reviewer feedback, written by step 1b, and is not needed here).

2. **Map each connection to its cache slug.**
   Slugs are short, uppercase, and fixed — not derived from the LinkedIn URL.
   Current mapping:

   | Connection                              | Group        | Slug         |
   |------------------------------------------|--------------|--------------|
   | ASIS New Zealand         | own          | ASISNZ      |
   | New Zealand Security Association (NZSA)  | associations | NZSA         |
   | ASIS International                       | associations | ASIS         |
   | NZ Police                                | associations | NZPOLICE     |
   | Johnson Controls                         | partners     | JOHNSON      |
   | Gallagher Security                       | partners     | GALLAGHER    |
   | Inner Range ANZ                          | partners     | INNERRANGE   |
   | Bosch Security and Safety Systems        | partners     | BOSCH        |
   | Integrated Control Technology (ICT)      | partners     | ICT          |
   | Jacques Technologies                     | partners     | JACQUES      |

   If `connections{}` ever gains an entry not in this table, pick a short
   uppercase slug the same way (first/most distinctive word, no spaces) and
   add it to this table in the same edit that adds the connection.

3. **Read the fetch log.**
   All connections share one append log, `MAY/LOG-<quarter>.log`
   (e.g. `MAY/LOG-2026Q3.log`) — newest entry first, just below the
   anchor marker. Each entry is two lines, headed by the fetch time and the
   connection's slug:

   ```
   ## <fetchedAt ISO timestamp> <SLUG>
   {"slug":"NZSA","companyName":"...","url":"...","fetchedAt":"...","followerCount":0,"bio":"...","recentPosts":[...]}
   ```

   To read the **most recent** entry for a slug (default): take the first
   `## <timestamp> <SLUG>` block for that slug after the anchor marker and
   parse the JSON line that follows it.

   To read the entry **closest to a specific date** (e.g. when auditing
   why a past batch made a particular selection): scan the `## <timestamp>
   <SLUG>` headers for that slug and pick the entry whose `fetchedAt` is ≤
   the target date and closest to it.

   The JSON shape within each entry:
   ```json
   {
     "slug": "NZSA",
     "companyName": "New Zealand Security Association (NZSA)",
     "url": "https://www.linkedin.com/company/new-zealand-security-association",
     "fetchedAt": "2026-10-20T03:00:00Z",
     "followerCount": 0,
     "bio": "string",
     "recentPosts": [
       { "date": "2026-10-18", "text": "string", "url": "string" },
       { "date": "2026-10-17", "text": "string", "url": "string", "repostOf": "Other Company Name" }
     ]
   }
   ```
   `repostOf` is present only when the connection reposted someone
   else's content — the text is still worth reading for relevance, but
   it's that other company's words, not the connection's own.

4. **Check freshness before trusting the data.**
   - **Missing file** — the Action hasn't run for this slug yet, or the
     connection is new. Treat as 1a's "inactive page" case: do not tag this
     connection in STEP 2, and note it as MISSING in the 1a findings.
   - **URL mismatch** — compare the entry's `url` field against that slug's
     URL in `CAN/TREE-2026Q3.json`'s `connections{}` *right now*. If they
     differ, treat as STALE regardless of `fetchedAt`'s age.
   - **Stale (`fetchedAt` more than 7 days old)** — flag as STALE in the 1a
     findings but still use the data; a week-old snapshot is still more
     current than guessing.
   - **Malformed entry** — flag as MISSING and skip; don't block the batch
     on one bad entry.

5. **Filter to the last 7 days, then summarize.**
   Before summarising, filter `recentPosts` to posts whose `date` is within
   the last 7 days (today − 7 days to today, inclusive). This is the same
   rolling window `gen_pr_body.py` uses for the PR's "Connection activity"
   section — keeping research and PR in sync so both fairly represent this
   week's signals.

   For each connection with posts in the window, write 1–2 sentences on
   anything relevant to the upcoming content angles — campaigns, product
   launches, awards, hiring pushes, partnership news.
   Connections with no posts in the window get a one-line "no activity (last 7 days)."

6. **Hand off to 1b.**
   Produce a short findings block (per-connection summary + any
   MISSING/STALE flags) and carry it into 1b subtype selection, per README
   rule 4: "subtype selection in 1b must be informed by what 1a found."

## Constraints

- Never call `fetch()` or any LinkedIn URL directly from this skill — that's
  exactly the unauthenticated path this design replaces.
- Never write or edit `MAY/LOG-<quarter>.log` from here — that file
  is owned by the `fetch-linkedin` GitHub Action.
- The quarter suffix (`2026Q3`) is hardcoded per the current quarter's key
  files; update it at quarter rollover alongside the rest of the files listed
  in README's QUARTER ROLLOVER section.
