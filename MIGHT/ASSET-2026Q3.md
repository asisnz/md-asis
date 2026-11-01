ASSET LOG

####### <!-- ANCHOR MARKER - ADD ALL NEW ASSET ENTRIES DIRECTLY BELOW THIS LINE -->

## ASSET:asis 2026-11-02 -> md-asis repo created and fully mirrored from md-redwolf; GitHub setup complete

**Context:** New client pipeline created for ASIS New Zealand (https://www.linkedin.com/company/asis-new-zealand) mirroring the md-redwolf / py-redwolf architecture. All Red Wolf branding, org references, and LinkedIn slugs replaced throughout.

**Local repos created:**
- `/Documents/GitHub/md-asis` — full copy of md-redwolf (py-redwolf subfolder excluded), all references updated: `redwolfnz` → `asisnz`, `md-redwolf` → `md-asis`, `py-redwolf` → `py-asis`, `Red Wolf High Level Security Ltd` → `ASIS New Zealand`, LinkedIn company slug → `asis-new-zealand`, slugs `REDWOLF` → `ASISNZ` in all scripts and skills.
- `/Documents/GitHub/py-asis` — copy of py-redwolf; same substitutions applied. Git-inited separately as a private repo.

**GitHub repos created under `asisnz` org:**
- `asisnz/md-asis` (public) — pushed from local; remote fixed from stale `redwolfnz/md-redwolf` origin.
- `asisnz/py-asis` (private) — created and pushed.

**Logo:** `asis-nz-logo.svg` moved from Downloads → `md-asis/logo.svg`; `index.html` updated from `logo.jpg` to `logo.svg`.

**GitHub Pages:** source set to `GitHub Actions`. `deploy-pages.yml` fixed: inject step now references `secrets.MD_ASIS` (was `secrets.MD_ASISNZ` from the clone).

**Secrets:** Fine-grained PAT `md-asis-review` created: resource owner `asisnz`, repo `md-asis` only, Contents: Read and write. Added to `asisnz/md-asis` as `MD_ASIS` (matching `MD_REDWOLF` convention in md-redwolf).

**Data reset:** `COULD/TABLE-2026Q3.csv` cleared to headers only — Red Wolf post data removed, ready for first ASIS NZ content batch.

**Mirror check:** file structure, all 5 workflows, all 6 scripts, both Claude skills, TREE JSON, LOG, `.gitignore` — all confirmed matching md-redwolf (adjusted for ASIS NZ names). Zero stray `redwolfnz`/`Red Wolf`/`md-redwolf` references remaining in any code file.

**Still open:**
- `config.js` local PAT — replace `__REVIEW_PAT__` with the real `md-asis-review` token for local browser access.
- GitHub Actions secrets not yet added: `LINKEDIN_FETCH_URL`, `LISTENER_SHARED_SECRET`, `GENERATE_CONTENT_URL` — mirrors md-redwolf, pointing to py-asis listener on the Mac mini.
- py-asis Mac mini setup not yet done: Cloudflare tunnel (new `py-asis` tunnel + hostname), `login_linkedin.py`, `.env`, LaunchAgents for listener + cloudflared.
- `CAN/TREE-2026Q3.json` connections — carried over from Red Wolf; update own/associations/partners for ASIS NZ as needed.

## ASSET:asis 2026-10-28 -> generate-content: first e2e run via listener; TODO adjust workflow to push to main

**Done:** `GENERATE_CONTENT_URL` repo secret set to the tunnel base URL (`https://redwolf.toigroup.co.nz`, no path; `gen_posts.py` appends `/generate-content`). Direct POST of a real payload to the live listener returned 6 valid posts in 98s (`validate_posts()` passed, no repeated subtypes). First workflow_dispatch run on `main`: run 40615215955.

**TODO (decision: push to main):** `generate-content.yml` currently creates `content/w<NN>-batch`, pushes it, and opens a PR into `main`. Adjust it to commit the generated rows to `COULD/TABLE-2026Q3.csv` directly on `main` instead, removing the branch creation, the PR body step and the `gh pr create` step. Reuse the push-with-rebase-retry block from `fetch-linkedin.yml` (concurrent bot commits to `main` are expected: feedback and cache refreshes). Note this drops the human review gate the PR gave; confirm that is intended before changing.

**Observed:** `CF_ACCESS_CLIENT_ID` / `CF_ACCESS_CLIENT_SECRET` are not set as secrets and the tunnel host answers the listener's own 404, so Cloudflare Access does not appear to be enforcing; `LISTENER_SHARED_SECRET` is the only auth in front of the listener. Generation took 98s against a 170s listener timeout and the Action's 180s client timeout.

## ASSET:asis 2026-10-28 -> generate-content listener built on the Mac mini; mirrors fetch-linkedin, runs `claude -p`

Closes the "Pending on Mac mini" item from the entry below. Supersedes its "key stored locally" assumption: no Anthropic API key is used.

**py-asis (private):**
- `listener.py` — new `POST /generate-content`. Same auth as `/fetch` (`X-Listener-Secret` behind CF Access), same `_run_lock`, same subprocess shape as `run_browse_linkedin`: runs `generate_content.py`, 170s timeout, non-zero exit or non-JSON stdout gives 502, an `error` key is passed through as 502 so the Action fails and no PR opens.
- `generate_content.py` (new) — reads the Action's payload on stdin, runs `claude -p` under the Mac mini's Claude login (`--system-prompt`, `--model claude-opus-5-5`, `--tools ""`, `--no-session-persistence`, `--setting-sources ""`, `--strict-mcp-config`), extracts the JSON array (tolerates code fences) and prints `{"posts": [...]}` or `{"error": ...}`. Absolute path `~/.local/bin/claude` because launchd's PATH is minimal; `CLAUDE_BIN` / `GENERATE_MODEL` in `.env` override.
- `.env.example` documents the optional overrides.

**md-asis:** `gen_posts.py` now sends the `generate-post/SKILL.md` text (frontmatter stripped) as `systemPrompt` in the payload, so the Mac mini never needs a `git pull` to stay current.

**Why `claude -p` and not the API:** the Console API key is a separate pay-per-token bill; `claude -p` runs on the existing Claude subscription login. Mirrors fetch-linkedin's design: Action to CF Tunnel to listener to subprocess. One deliberate difference: a failed generation stops the run (all 6 pillars are required) rather than skipping like a failed connection.

**Verified:** real payload from `build_payload()` (10 connections, 18 used subtypes, 37 KB) through `generate_content.py` in 83s returned 6 posts, one per pillar; `validate_posts()` passed and no subtype repeated. Endpoint error paths (400, 401, error pass-through) checked against a stub.

**Not yet verified:** the call via the launchd-run listener (Claude login under launchd), the Action's POST over the tunnel, and the `GENERATE_CONTENT_URL` secret / tunnel route to `:8787`. Listener needs a restart to pick up the new code. One generated PEOPLE post shortened a person's name to "R." in the title; check in the review PR.

## ASSET:asis 2026-10-28 -> generate-content: Claude API call routed through Mac mini

`gen_posts.py` updated to POST the generation payload to the Mac mini listener via Cloudflare Tunnel instead of calling the Anthropic API directly. Mac mini handles the Claude call (key stored locally) and returns a JSON array of 6 posts. `generate-content.yml` now uses `pip install requests` and the same 4 CF tunnel secrets as `fetch-linkedin` (`GENERATE_CONTENT_URL`, `CF_ACCESS_CLIENT_ID`, `CF_ACCESS_CLIENT_SECRET`, `LISTENER_SHARED_SECRET`). No `ANTHROPIC_API_KEY` in GitHub secrets required.

Pending on Mac mini: `listener.py` needs a `/generate-content` endpoint that reads the payload, calls Claude with `.claude/skills/generate-post/SKILL.md` as system prompt, and returns `{"posts": [...]}` or a bare array.

## ASSET:asis 2026-10-28 -> Pipeline restructure: step-2 is now generate-content (automated)

**PIPE-2026Q3.yml updated** — two-step structure:
- `step-1: fetch-linkedin` (1a only) — Mac mini / py-asis, cron Monday
- `step-2: generate-content` (1b + 1c + 2 combined) — Claude API, cron Tuesday

**New files created:**
- `.github/workflows/generate-content.yml` — cron Tuesday 8am NZST; creates `content/w<NN>-batch` branch, runs `gen_posts.py`, commits TABLE CSV, opens PR via `gh pr create`
- `.github/scripts/gen_posts.py` — reads TREE JSON + MAY logs, calls `claude-opus-4-8`, validates 6-post JSON response (no `--`, all 6 pillars, no repeated subtypes), appends rows to TABLE CSV with `csv.QUOTE_ALL` serialization
- `.claude/skills/generate-post/SKILL.md` — system prompt for the generation call; covers angle selection, media-type decision, brand voice rules, NZ framing, and exact JSON output format

**Reasoning for merge:** Steps 1b (select-topic), 1c (choose-artifact), and 2 (write) are pure Claude reasoning. Only 1a requires the Mac mini (residential IP + Playwright). Combining them cuts latency and eliminates a hand-off artifact.

## ASSET:asis 2026-10-27 -> Feedback: direct CSV write via Contents API PUT (~1–2s)

Replaced `repository_dispatch` → `update-feedback.yml` (~15–20s) with a direct PUT to the GitHub Contents API. SHA tracked globally (`csvSha`) and updated after each write. `csvRows` and `csvHeaders` held in memory for serialization. `serializeCSV()` replicates Python `csv.QUOTE_ALL`. `update-feedback.yml` workflow left in place but no longer active — can retire next quarter rollover.

## ASSET:asis 2026-10-27 -> UI/data fixes: PDF preview, CSV freshness, feedback persistence

**PDF preview:** Replaced Google Docs Viewer iframe (triggered "viewer" save-as) with `<embed type="application/pdf">` loaded via blob URL. Raw.githubusercontent.com serves files as `application/octet-stream` — switched all media URLs to `https://asisnz.github.io/md-asis/` (GitHub Pages serves correct MIME types).

**CSV freshness:** Switched CSV fetch from `raw.githubusercontent.com` (5-min CDN cache) to GitHub Contents API (authenticated — no CDN cache). `CSV_PATH` constant added; raw URL kept as unauthenticated fallback.

**Feedback persistence:** Win/Tie/Lost saves via `repository_dispatch` → `update-feedback.yml`. localStorage overlay added then removed once root cause (CDN cache) was fixed. Current state: no localStorage, API fetch always fresh.

## ASSET:asis 2026-10-27 -> UI comment feature unparked; save-file symptom under monitoring

**Comment feature:** `.feedback-comment-row` and `.saved-comment` were parked (`display:none !important`). Unparked — now live. Saves to `feedback-comment` column in `COULD/TABLE-2026Q3.csv` via `update-feedback.yml` dispatch.

**Save-file symptom (monitoring):** Prod URL (`https://asisnz.github.io/md-asis/`) serves correct `text/html` headers. No code-level cause found. Suspected: client-side (browser app, wrong raw URL, or Edge SmartScreen). Monitoring — investigate further if reported again.

## ASSET:asis 2026-10-27 -> Folder swap: COULD↔MAY (commit c5b2046)

**New semantics:**
```
COULD: assets and values   # what the content could reference  (was MAY)
MAY:   posts and media     # what the content should contain   (was COULD)
```

**Files moved (57 total):**
- `MAY/TABLE-2026Q3.csv` → `COULD/TABLE-2026Q3.csv`
- `COULD/<SLUG>-2026Q3.log` × 11 → `MAY/<SLUG>-2026Q3.log`
- `COULD/media/2026Q3/` → `MAY/media/2026Q3/` (45 files)

**References updated:** `PIPE-2026Q3.yml`, `gen_pr_body.py`, `fetch_linkedin_cache.py`, `fetch-linkedin.yml`, `update-feedback.yml`, `SKILL.md`, `index.html`.

## ASSET:asis 2026-10-27 -> PR body: Connection activity section; LOG-2026Q3.log retired from pipeline

**Connection activity section added to gen_pr_body.py:**
New section between CAN tree and MAY posts (CAN → COULD → MAY → MIGHT order). Reads each `COULD/<SLUG>-2026Q3.log`, parses the most recent fetch entry, filters `recentPosts[]` to the last 7 days (rolling window anchored to today), and shows only connections that had posts in that window. Empty connections omitted. Fallback: `_No connection posts in the last 7 days (<start> – <end>)._`

**Window: last 7 days (not ISO week-1):**
Initially implemented as the previous ISO week (w-1 Mon–Sun). Revised to a rolling 7-day window anchored to today — simpler, no ISO boundary arithmetic, and fairly labelled as this week's signals regardless of batch day. Same window applied to `SKILL.md` step 5 so research and PR are in sync.

**SKILL.md step 5 updated:**
Now filters `recentPosts` to posts within the last 7 days before summarising, matching the PR section. Connections with no posts in window: "no activity (last 7 days)."

**COULD/LOG-2026Q3.log retired from active pipeline:**
Removed from `gen_pr_body.py` (LOG const, `log_entry()` function, "Activity log" PR section), `PIPE-2026Q3.yml` (step 2a files, step 2b git_add, key_files, quarter_rollover). File left in repo with v1/v2/v3 history intact — not deleted.

## ASSET:asis 2026-10-27 -> README.md → PIPE-2026Q3.yml; LOG restructured; JSON caches → append-only logs

**README.md → PIPE-2026Q3.yml + gen_pr_body.py:**
README.md deleted. Replaced by two files:
- `PIPE-2026Q3.yml` — full pipeline definition as YAML; all prose kept as `#` comments; PR template section replaced by reference to the script below.
- `.github/scripts/gen_pr_body.py` — generates PR body dynamically from live data files for Step 2b. Reads `MAY/TABLE-2026Q3.csv` (posts table), `COULD/LOG-2026Q3.log` (feedback block), `MIGHT/ASSET-2026Q3.md` (assets entry), calls `gen_tree_mermaid.py` subprocess for the Mermaid block. Usage: `python3 gen_pr_body.py <NN> > /tmp/pr_body.md`. Sections order: CAN tree → COULD log → MAY posts → MIGHT assets.

**COULD/LOG-2026Q3.log restructured as versioned feedback log:**
Repurposed from generic activity log to one versioned entry per client-visible batch, newest first, anchor marker. Each entry: `## v<N> — w<NN> — <date>` header + posts table with Feedback column. Backfilled: v1 (w42), v2 (w43), v3 (w44 — Feedback column set to `—` pending results).

**CAN/TREE-<SLUG>-2026Q3.json → COULD/<SLUG>-2026Q3.log (10 files, commit 9b0ad81):**
All 10 per-connection JSON snapshots deleted from `CAN/`. Replaced by append-only logs in `COULD/` — newest entry first, anchor marker, each entry = `## <fetchedAt ISO>` + compact JSON line. Existing 2026-10-25 snapshot migrated as the first entry in each log.

Files deleted from CAN/: `TREE-{ASISNZ,NZSA,ASIS,NZPOLICE,JOHNSON,GALLAGHER,INNERRANGE,BOSCH,ICT,JACQUES}-2026Q3.json`
Files created in COULD/: `{ASISNZ,NZSA,ASIS,NZPOLICE,JOHNSON,GALLAGHER,INNERRANGE,BOSCH,ICT,JACQUES}-2026Q3.log`

**fetch_linkedin_cache.py updated:**
Overwrite-JSON replaced by `prepend_entry()` — prepends a new `## <fetchedAt> / <compact JSON>` block after the anchor. Output path changed from `CAN/TREE-<SLUG>-2026Q3.json` to `COULD/<SLUG>-2026Q3.log`. `_remove_orphaned_cache_files()` removed (history is the point). Malformed-log fallback: appends at end if anchor is missing.

**References updated:**
- `fetch-linkedin.yml`: `git add -- 'COULD/*-2026Q3.log'` (was `CAN/TREE-*-2026Q3.json`)
- `SKILL.md`: new file path + most-recent vs by-date lookup instructions
- `PIPE-2026Q3.yml`: key_files section

**content/w44-batch merged to main; branch deleted:**
User preference: main only. Branch fast-forwarded. One CSV conflict during merge resolved: kept all 18 rows from HEAD (w44 data), applied post-008 feedback-comment clear from origin/main. Branch deleted local and remote.

## ASSET:asis 2026-10-27 16:20 -> Week 44 media generated (post-013, 014, 015, 017, 018)

**Media (COULD/media/2026Q3/, 1080x1350; media URLs updated in MAY/TABLE-2026Q3.csv):**
- post-013 https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-013-iqp-compliance.png — compliance schedule → IQP inspection (latch/lock/release incl. alarm activation and power failure) → fix → Form 12A → BWOF; year-end prompt.
- post-014 https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-014-govt-policy.png — Minister Mitchell at ASIS NZ chapter meeting (October) + short ASIS NZ quote, PSR areas and who it applies to.
- post-015 https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-015-active-assailant.png — "<50%" stat + four factors from the ASIS/Everbridge study (CAN/TREE-ASIS 2026-10-22).
- post-017 https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-017-govt-case-study.pdf (+ post-017-govt-slide-1..5.png) — site, challenge, design, install, outcome.
- post-018 https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-018-awareness-final-week.gif — 6.5 s loop: "Your alarm goes off at 2am on a Sunday" → three checks tick on → CTA.
- post-016 jpg — placeholder file added (https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-016-PLACEHOLDER.md); needs a real photo of Shamal Kumar with consent.

**Kept to confirmed facts:**
- post-014: the NZSA cache shows the Minister's ASIS NZ appearance was *announced* for October; nothing on what he said. Graphic does not claim policy changes or that the PSR is evolving.

**Verify before publishing:**
- post-013: "ASIS New Zealand holds IQP qualifications" — confirm IQP registration with each council. Official term is "independent qualified person".
- post-014 copy: "just briefed security leaders on policy changes" / "PSR obligations are evolving" — unconfirmed.
- post-017: real government client — confirm facts (Integriti, NOC monitoring, resilient connectivity, "certified to the performance requirements") and client approval. No client named.
- post-018: graphic and copy offer a free 30-minute system review call in November — confirm the offer is real.

**Note:** old week 41 files post-013-access-control.png … post-018-did-you-know.png are still in COULD/media/2026Q3/ unreferenced.

## ASSET:asis 2026-10-27 -> Repo housekeeping: folder renames, README.TXT→README.md, step restructure

**Folder renames (git mv — all references updated):**
- `COULD/TABLE-2026Q3.csv` → `MAY/TABLE-2026Q3.csv`
- `MAY/ASSET-2026Q3.md` → `MIGHT/ASSET-2026Q3.md`
- `MIGHT/LOG-2026Q3.log` → `COULD/LOG-2026Q3.log`

References updated in: `README.md`, `index.html`, `update-feedback.yml`, `fetch-linkedin.yml`, `fetch_linkedin_cache.py`, `SKILL.md`. Historical entries in this log left intact.

**README.TXT → README.md:**
Plain text converted to Markdown — headers, tables, fenced code blocks, collapsible PR template. All `README.TXT` functional references updated to `README.md`.

**Step restructure:**
- Steps B / 3 / 4 / 5 collapsed into Step 2 sub-steps (2a–2e).
- New **Step 2a**: checklist to update TREE / LOG / CSV / ASSET before committing.
- **Step 2b** (Open Weekly PR): PR template expanded with dedicated sections for Posts, Activity log, Assets, and Content Strategy Tree.
- Removed **Review** step (was 2d) — formal review gate dropped.
- Removed **Publish** step (was 2e) — orchestration now ends at media.

Final step structure: Step 1 (Research 1a/1b/1c) → Step 2 (Generate) → 2a (Update files) → 2b (Open PR) → 2c (Media).

## ASSET:asis 2026-10-27 -> Week 44 batch generated; PR #1 opened with auto-updating Mermaid content tree

**Week 44 content batch — post-013 to post-018 (all BLOCKED pending media):**

| Post | Pillar | Type | Subtype | Score | Media |
|------|--------|------|---------|-------|-------|
| post-013 | SERVICES | Consulting & Design | IQP Inspections | 7 | png |
| post-014 | INDUSTRY | Regulation & Compliance | Government Policy | 8 | png |
| post-015 | AUTHORITY | Thought Leadership | Expert Opinion | 8 | png |
| post-016 | PEOPLE | Team Spotlight | Staff Profiles | 7 | jpg |
| post-017 | TRUST | Case Studies | Govt & Critical Infrastructure | 9 | pdf |
| post-018 | ENGAGEMENT | Campaigns & Seasonal | Security Awareness Month | 8 | gif |

**Step 1a signals that drove selection:**
- NZSA (Oct 15): Minister Mitchell at ASIS NZ event on PSR/legislative changes → post-014
- ASIS (Oct 22): <50% of orgs confident in active assailant response → post-015
- ASISNZ/NZSA: Shamal Kumar NZSA finalist; awards spotlight concluded Oct 19 → post-016
- INNERRANGE (Oct 21): SAGE 2026 govt/defence expo Nov 19 → post-017
- Seasonal: final week of Security Awareness Month → post-018; end-of-year IQP compliance window → post-013
- BOSCH: confirmed dead (Keenfinity Group since Jul 2026) — not tagged
- JACQUES: last post Jun 2026 — not tagged

**PR #1 opened:** https://github.com/asisnz/md-asis/pull/1 (branch `content/w44-batch`)

**GitHub Action added — `.github/workflows/update-tree-mermaid.yml`:**
Triggers on push to main when `CAN/TREE-2026Q3.json` changes. Regenerates a `graph LR` Mermaid diagram from the JSON using `.github/scripts/gen_tree_mermaid.py` and replaces the `<!-- TREE-START -->` / `<!-- TREE-END -->` section in any open PR descriptions via `.github/scripts/replace_tree_section.py`. The PR description carries the content tree as a live visual reference for client review; no `.md` file is committed to `CAN/`.

**Verify before publishing:** all 6 posts BLOCKED — media briefs only, no files generated yet.

## ASSET:asis 2026-10-23 23:15 -> Week 43 v4 media: post-007 gif, post-008 png, post-011 pdf (commit 514bbd7)

**Generated (1080x1080, per briefs):**
- post-007 https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-007-failover-animation.gif — 6.2 s loop: Ethernet connected → connection lost → 4G LTE takes over → "Zero interruption. Dual-SIM failover built in." → primary restoring. Alarms / video / remote access stay ONLINE throughout. Footer credits Inner Range T4000 Pro (features per CAN/TREE-INNERRANGE 2026-10-02: 4G LTE + Ethernet + Wi-Fi, dual-SIM automatic failover, uninterrupted alarm reporting).
- post-008 https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-008-itot-convergence.png — Physical security vs IT/OT Venn with the governance gap questions.
- post-011 https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-011-residential-case-study.pdf (+ post-011-residential-slide-1..5.png) — brief, challenge (indicative floor plan), system, install, outcome + CTA.

**Still placeholders (cannot be generated):** post-009 jpg (real team photo with NZSA certificate), post-010 mp4 (real team footage), post-012 png (needs real poll results).

**Deviations from briefs:**
- post-008: "Most NZ organisations have no answer." replaced with "Does your organisation have an answer?" (no source for the claim). No URL added (redwolf.net.nz still unverified).
- post-011: camera count "[X]" omitted (unknown). Anonymised client quote "We didn't know security could look like this." NOT used — add only if it is the client's real words with written approval. No install photos available; slide 4 uses a step list instead. Floor plan is indicative, not the real layout.

**Verify before publishing:** post-011 project facts (Wellington, neighbouring incidents, heritage constraints, concealed install, systems installed) and client approval. post-010 copy "grown 11%" comes from LinkedIn hiring insights in the ASISNZ cache — confirm.

## ASSET:asis 2026-10-23 -> Week 43 v4 redo — media briefs (v4, live cache batch)

v2 media files removed (orphaned by redo). New placeholders created for v4 angles.
5 distinct media types this batch: gif, png, jpg, mp4, pdf, png — satisfies rule 8.

**post-007** SERVICES / Monitoring & Response / Systems Monitoring — score 7
File: post-007-failover-animation.gif
Brief: Looping animated diagram — Ethernet primary path active, Ethernet drops (red flash), 4G LTE failover kicks in (green), alarm/video/remote access icons stay lit throughout. Inner Range T4000 Pro label. Approx 4–6s loop. ASIS New Zealand brand palette.

**post-008** INDUSTRY / Threat Intelligence / Cybersecurity Convergence — score 8
File: post-008-itot-convergence.png
Brief: Venn/split diagram — Physical Security (CCTV, access, alarm icons) overlapping IT/OT (server, firewall, switch icons). Overlap zone labelled "Governance Gap" with three questions: who owns firmware updates, network credentials, device audits. Headline: "Your CCTV is on the network. Is your IT team responsible for it?" Dark background. ASIS New Zealand branded.

**post-009** AUTHORITY / Accreditations & Partnerships / NZSA Membership — score 8
File: post-009-nzsa-membership.jpg
Brief: Real team photo — ASIS New Zealand staff in uniform or professional attire, Wellington or Auckland setting. NZSA membership context visible (certificate, logo). No stock photography. Optional overlay: NZSA member badge corner, ASIS New Zealand logo bottom right.

**post-010** PEOPLE / Careers / Career Growth — score 8
File: post-010-career-growth.mp4
Brief: 30–60s recruitment video. Opening: ASIS New Zealand van on site. Team member 1: career path (8–10s). B-roll: install work. Team member 2: culture (8–10s). Closing card: "We're growing. Join the team." + CTA. Subtitles required (muted-play). Real team, real sites only.

**post-011** TRUST / Case Studies / Residential — score 9
File: post-011-residential-case-study.pdf
Brief: 5-slide carousel — (1) client context/brief, (2) security challenges (multi-entry, heritage constraints, family usability), (3) system components (CCTV, access control, alarm, single-app integration), (4) installation highlights (concealed cabling, aesthetic hardware), (5) outcome + anonymised quote. Anonymise all client-identifying details. ASIS New Zealand palette throughout.

**post-012** ENGAGEMENT / Interactive / Questions & Debates — score 7
File: post-012-poll-results.png
Brief: Poll results graphic — 4 percentage bars for poll answers (DRAFT: bars empty until real results available). ASIS New Zealand commentary below top result. Note: DO NOT publish until actual poll results from LinkedIn post-006 are confirmed.

## ASSET:asis 2026-10-23 22:40 -> Week 43 v3 media generated from briefs (commit 906a677)

**Media (COULD/media/2026Q3/, 1080x1350, replaces the .png.md placeholders; table URLs unchanged):**
- post-007 https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-007-access-control-layers.png — 4 layers (credentials, door hardware, zone logic, integrations) + self-service scheduling callout. No partner brand colours used (avoids implying endorsement).
- post-008 https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-008-psr-govt-policy.png — PSR covers / applies to / why it matters now.
- post-009 https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-009-partner-updates-ir-gallagher.png — IR Connect 3.9.0 vs Gallagher SMB features.
- post-010 https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-010-culture-high-level.png — Precision, Ownership, Availability, Accountability (brief wording).
- post-011 https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-011-govt-case-study-carousel.pdf + post-011-slide-1..5.png — brief, approach, system, outcome, CTA.
- post-012 https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-012-poll-results.png — **DRAFT, watermarked**, no percentages.

**Verified against CAN/ caches:** Gallagher Self-service Access Schedules + Duress Code (TREE-GALLAGHER 2026-10-16); IR Connect 3.9.0 camera search, performance, Android/iOS (TREE-INNERRANGE 2026-10-14); Mark Mitchell ASIS NZ chapter meeting (TREE-NZSA 2026-10-15, reposting ASIS NZ).

**Deviations from brief:**
- post-008: PSR shown with its 4 areas (governance, personnel, information, physical), not 3. "Who it applies to" corrected: mandated for public service agencies, NZ Police, NZDF, NZSIS; benchmark for Crown entities, suppliers, critical infrastructure. Column 3 shows only what the cache supports — the cache announces the Minister *will* attend; it says nothing about PSR changes. CTA softened from "We design to PSR" to "Ask us how we can help".
- post-012: brief values were labelled mock. Rendered as a DRAFT with "??%" bars and placeholder commentary. Options taken from the post-006 graphic (Outdated CCTV, Weak access control, No 24/7 monitoring, No security assessment) — brief listed different options; confirm which options the live LinkedIn poll actually used. Re-render with real numbers before publishing (POLL list in build script).

**Verify before publishing:**
- post-008 copy says the Minister "recently addressed" ASIS NZ — cache only confirms he was due to attend in October. Confirm it happened. Copy also says "The PSR framework is evolving" — no source found.
- post-011: confirm project facts (Inner Range Integriti, zone segregation, encrypted audit trail, single credential, operations uninterrupted) and client approval; no client named.
- post-010: "After 20 years" in copy still unverified.

## ASSET:asis 2026-10-23 -> Week 43 media briefs (v3 redo — live cache batch)

All six posts BLOCKED pending media. Placeholders created in COULD/media/2026Q3/.

**post-007** SERVICES / Electronic Security / Access Control — score 7
File: post-007-access-control-layers.png
Brief: Layered diagram showing a complete access control system — four horizontal layers:
  1. Credentials (key card, PIN, mobile, biometric)
  2. Door hardware (reader, strike, controller)
  3. Zone logic (permission maps, time schedules, Gallagher self-service scheduling callout)
  4. Integrations (CCTV link, alarm link, audit trail / reporting)
Branded ASIS New Zealand style. Subtle Gallagher and Inner Range colour accents in the hardware layer.
Tone: clear, technical, confidence-building.

**post-008** INDUSTRY / Regulation & Compliance / Government Policy — score 8
File: post-008-psr-govt-policy.png
Brief: PSR framework summary card. Headline: "Protective Security Requirements — What Organisations Need to Know Now."
Three columns: (1) What the PSR covers (people, information, physical), (2) Who it applies to (government agencies, critical infrastructure, suppliers), (3) What's changing (legislative context from Mark Mitchell ASIS NZ appearance). ASIS New Zealand brand footer: "We design to PSR. Ask us how." Clean, authoritative layout.

**post-009** AUTHORITY / Accreditations & Partnerships / Supplier Partnerships — score 8
File: post-009-partner-updates-ir-gallagher.png
Brief: Side-by-side partner update card. Left panel (Inner Range): headline "IR Connect 3.9.0" with three bullet callouts — camera search across large deployments, performance improvements, Android + iOS. Right panel (Gallagher): headline "New SMB Features" — Self-service Access Schedules (facility managers, no callout needed), Duress Code (silent distress signal). Both panels share ASIS New Zealand brand footer: "We install and support both. Ask us what's right for your site."

**post-010** PEOPLE / Culture & Values / Company Culture — score 8
File: post-010-culture-high-level.png
Brief: Values card. Headline: "What High Level Security Means to Us." Four quadrants, each with a bold one-word value and one supporting sentence:
  PRECISION — "Every system we design is spec'd for the site, not off a shelf."
  OWNERSHIP — "We take responsibility for outcomes, not just deliverables."
  AVAILABILITY — "Our clients can reach us when something goes wrong, not just when it's convenient."
  ACCOUNTABILITY — "Every install is documented. Every outcome is measurable."
ASIS New Zealand brand colours. Clean, confident. No stock imagery.

**post-011** TRUST / Case Studies / Government & Critical Infrastructure — score 9
File: post-011-govt-case-study-carousel.pdf (+ slides 1–5 as separate PNGs)
Brief — 5 slides:
  Slide 1 (Challenge): Wellington government facility. Ageing access control, no PSR-compliant audit trail, multiple legacy credential types in use. Headline: "The Brief: PSR Compliance Without Disruption."
  Slide 2 (Approach): Site assessment → zone mapping → phased replacement → integration with existing CCTV. Headline: "Designed Around Their Operational Constraints."
  Slide 3 (System): Inner Range Integriti platform, zone segregation, encrypted audit trail, CCTV integration. Hardware list. Headline: "The System We Delivered."
  Slide 4 (Outcome): PSR-compliant documentation, full audit trail, single-credential access across all zones. Headline: "The Outcome."
  Slide 5 (CTA): "Facing a PSR review or upgrade? We have done this before." Contact prompt + ASIS New Zealand logo.
All slides branded. No client name used.

**post-012** ENGAGEMENT / Interactive / Questions & Debates — score 7
File: post-012-poll-results.png
Brief: Poll results graphic. Headline: "NZ Businesses Told Us Their Biggest Physical Security Gap." Four horizontal percentage bars (mock values until real poll data available — update before publishing):
  Outdated credentials / no access review — 38%
  Unmonitored visitor access — 27%
  Propped or tailgated doors — 22%
  No 24/7 monitoring — 13%
Below bars: ASIS New Zealand commentary box — "Our take: the top answer is fixable in a day. Most organisations just haven't prioritised it yet." ASIS New Zealand brand colours. Feels data-driven, not promotional.

## ASSET:asis 2026-10-23 -> py-asis added as a submodule of md-asis; listener now runs from it

**Change:** `asisnz/py-asis` (private) is now a git submodule of `md-asis` at
`py-asis/`, pinned to `c25b9ca` (md-asis commit `097717f`). README.TXT updated to
match (`a594857`).

**Listener migration:**
1. Built a fresh `.venv` inside the submodule from `requirements.txt` (Playwright).
2. Copied `.env` and `linkedin_storage_state.json*` (all gitignored, never committed)
   from the standalone `~/Documents/GitHub/py-asis` into the submodule.
3. Rewrote `~/Library/LaunchAgents/com.asisnz.linkedin-listener.plist` so the venv
   Python, `listener.py`, WorkingDirectory and log paths point at
   `md-asis/py-asis/`. Old plist kept as `.plist.bak-standalone`.
4. Reloaded the agent. It is running from the new path and answers on
   `127.0.0.1:8787`.

**Unchanged:** the tunnel plist and `~/.cloudflared/py-asis.yml` (they don't
reference the repo path), and all three workflows (none use `submodules:`, and
`md-asis` is public while `py-asis` is private, so Actions can't and
shouldn't fetch it).

**Verified:** manual `fetch-linkedin` run (workflow_dispatch, run 39899910704)
succeeded end to end from the submodule listener: 10/10 connections returned
3-5 real recentPosts each, committed as `b859a3a`; `py-asis/listener.log`
shows every slug served from the new path.

**Cleanup:** the standalone `~/Documents/GitHub/py-asis` was deleted after the
verified run (it had no uncommitted or unpushed work).

## ASSET:asis 2026-10-23 -> Fix: GitHub Pages legacy mode was bypassing PAT injection — 401 resolved

**Root cause:** After the org transfer, GitHub Pages was set to `build_type: legacy` (serve
directly from the main branch). The `deploy-pages.yml` workflow was running and succeeding, but
its artifact was never served — Pages was reading `index.html` straight from the committed file,
which contains the literal string `__REVIEW_PAT__`. TOKEN resolved to `""` on every page load,
causing HTTP 401 on every feedback dispatch.

**Fix applied:**
1. Switched Pages build type from `legacy` to `workflow` via the GitHub API (`PUT /repos/asisnz/md-asis/pages` with `build_type=workflow`).
2. Updated `MD_ASISNZ` secret to the known-good PAT (config.js value confirmed working).
3. Added `workflow_dispatch` trigger to `deploy-pages.yml` so redeploys can be triggered without a push.
4. Triggered a fresh deploy — Actions artifact now served at https://asisnz.github.io/md-asis/ with PAT injected.

**Other fixes in same session:**
- `index.html` OWNER constant: `jayreck996` → `asisnz` (dispatch and CSV fetch were hitting wrong org).
- `COULD/TABLE-2026Q3.csv` + `MAY/ASSET-2026Q3.md`: all functional `raw.githubusercontent.com/jayreck996` URLs updated to `asisnz`.
- `update-feedback.yml`: added `git pull --rebase` before `git push` to fix push-rejection race condition on concurrent feedback events.
- Local git remote updated from `jayreck996/md-asis` to `asisnz/md-asis`.

## ASSET:asis 2026-10-23 -> Owner references updated from jayreck996 to asisnz

Post-org-transfer cleanup: all functional `jayreck996` references replaced with `asisnz`.

**Files changed:**
- `index.html` — `OWNER` constant corrected from `"jayreck996"` to `"asisnz"`; fixes GitHub API dispatch and CSV fetch pointing to the wrong org.
- `COULD/TABLE-2026Q3.csv` — all 12 `media URL` values updated from `raw.githubusercontent.com/jayreck996/` to `raw.githubusercontent.com/asisnz/`.
- `MAY/ASSET-2026Q3.md` — all functional raw.githubusercontent.com and github.com media URLs updated to `asisnz`; historical migration log text (personal account references, transfer records) left intact as accurate history.

**Remaining jayreck996 references:** historical text only in this file — migration notes, org transfer record, risk flags written at the time. Correct as written; not touched per append-only log rule.

## ASSET:asis 2026-10-22 -> Post-cycle refinements: real recentPosts quality, account swap, connections{} drift protection

Follow-up to the prior entry's "9/10 connections, most posts empty"
result — pushed on whether that was really "enough," which it wasn't.

**recentPosts fixes (py-asis, several commits), each caught by
testing against real pages before shipping:**
  - "Follow" button text leaking into post content (pages not already
    followed show it inline) — stripped.
  - Biggest gap: the extraction only recognized small pages' "Feed
    post" label layout. Large/corporate pages (e.g. Johnson Controls,
    3.8M followers, posts multiple times a day) use a completely
    different layout — one "Page posts" header, no per-post label —
    and silently returned 0 posts, which looked like a quiet account
    but wasn't. Rewrote to detect posts by pattern (company name
    directly followed by a date-shaped line) instead of either page's
    specific label. Fixed all 7 connections that had shown 0 posts.
  - Acronym mismatch: "Inner Range ANZ" (official) vs. "Inner Range
    Australia & New Zealand" (displayed) — fixed with an
    initials-based check, but only after catching that a naive
    "2+ shared words" version would have misattributed a REPOST from
    a different region ("Inner Range North America") as this
    connection's own words.
  - Last post on a page (no "more" marker, no next post to bound it)
    ran into sidebar/footer content — added explicit stops.
  - Reposts are now captured (not filtered out) — tagged with
    `repostOf` so they're never confused with the connection's own
    words. Schema documented in the skill.

**Re-ran fetch-linkedin.yml 3 times** as these landed, each getting
closer to complete; final run: all 10 connections have real data,
INNERRANGE (previously 0) now has 5 real posts including one correctly
excluded-then-correctly-included repost.

**Real operational mistake made and fixed:** triggered a new run,
then kept committing to md-asis while it was still in flight — its
own `git push` got rejected (unrelated commits had moved `main`) and
the entire run's fetched data was lost, not just delayed. Root-caused
and fixed below.

**Account swap:** switched which LinkedIn account `browse_linkedin.py`
authenticates as. `login_linkedin.py` now backs up the previous
session before overwriting it (new, since this was the first real
account change) rather than discarding it silently.

**connections{} can change at any time — caches could silently drift
from it.** Raised directly: `CAN/TREE-2026Q3.json`'s `connections{}`
can be edited whenever (a partner's page migrating, a corrected
slug), but nothing checked whether a cache file's `url` still matched
the CURRENT entry — only time-based staleness existed, which can't
catch this. Fixed three things together:
  1. `fetch-linkedin` skill: a cache whose `url` no longer matches
     `connections{}`'s current entry for that slug is now STALE
     regardless of `fetchedAt`'s age.
  2. `fetch_linkedin_cache.py`: removes `CAN/TREE-<SLUG>-2026Q3.json`
     for any slug no longer in `connections{}`, instead of leaving
     orphaned files indefinitely.
  3. The git-push race above: the commit step now retries with
     fetch+rebase instead of a bare push that fails outright.
  Confirmed a URL *change* (same slug) already worked correctly
  without any fix — the Action reads `connections{}` fresh every run.
  Flagged but not yet fixed: a *rename* (not just URL/content change)
  breaks `SLUG_MAP`'s name-keyed lookup and would cause the new
  orphan-cleanup to delete that connection's cache as if it were
  genuinely removed, even though it still conceptually exists.

**README fixes along the way:** a stale fallback note still said the
pipeline was "pending" after it had gone live; STEP 1a never mentioned
reading the base `CAN/TREE-2026Q3.json` for the connection list itself,
only the per-slug cache files.

**Status:** real, complete data for all 10 connections, verified.
`SLUG_MAP` rename-safety is an open, flagged gap, not yet fixed.

## ASSET:asis 2026-10-22 -> Full cycle completed for real: GitHub Action → Cloudflare → py-asis → real LinkedIn data → committed

**login_linkedin.py run successfully** (by the user). First attempt
was blocked by LinkedIn/Google ("This browser or app may not be
secure") — Playwright's bundled Chromium carries automation markers
that trip this check even for a genuine human login. Fixed by
switching both `login_linkedin.py` and `browse_linkedin.py` to
`channel="chrome"` (the real, already-installed Google Chrome, not
Playwright's own build) — also means `playwright install chromium` is
no longer needed at all (py-asis commit `69c91f4`).

**Implemented real bio/followerCount/recentPosts extraction**
(py-asis `d399883`, `48e43cb`), verified against real authenticated
fetches of ASIS New Zealand's own page:
  - `networkidle` never fires on LinkedIn (constant background
    polling) — switched to `domcontentloaded` + a fixed wait.
  - `recentPosts`: no stable CSS hook, but every post is reliably
    preceded by the literal visible text "Feed post" (an accessibility
    label). Splitting on that, keeping only chunks whose author line
    roughly matches companyName, filters out ad/promoted cards using
    the same label. Dates are best-effort (relative "Xd"/"Xw" or bare
    "Mon DD", no year given).
  - Bug caught and fixed: the company-name check was exact-string —
    `CAN/TREE-2026Q3.json`'s official names (e.g. "ASIS New Zealand High Level
    Security **Ltd**") don't match the shorter name LinkedIn actually
    displays ("ASIS New Zealand High Level Security"), which silently dropped
    every real post with no error. Fixed with a substring-containment
    check after normalizing punctuation/case.
  - `bio`: lives on a separate `/about/` page (the authenticated
    default view redirects the base URL to the Posts tab instead), no
    CSS hook either — plain text after the visible "Overview" label.

**Ran the real fetch-linkedin.yml Action, twice:**
  - 1st run (`39731202984`): all 10 connections came back **HTTP 403**
    — isolated to `urllib.request`'s default User-Agent
    ("Python-urllib/3.x") being blocked outright, before ever reaching
    the tunnel/listener. Reproduced with curl spoofing the same UA
    (blocked identically) vs. a normal UA (200) — most likely
    Cloudflare's Bot Fight Mode or a similar default WAF rule. Fixed
    by setting an explicit User-Agent (`md-asis` commit `8f474f0`).
  - 2nd run (`39731937253`): **9 of 10 connections got real data** —
    `CAN/TREE-<SLUG>-2026Q3.json` now has real `followerCount`/`bio`
    for NZSA, ASIS, NZPOLICE, JOHNSON, GALLAGHER, INNERRANGE, BOSCH,
    ICT, JACQUES (ASIS and BOSCH also got 1 real post each; the rest
    got 0 — genuinely quiet accounts, or the "Feed post" heuristic
    doesn't catch how larger companies' feeds render; honestly
    unknown which). ASISNZ alone got a navigation timeout — almost
    certainly from this session's own repeated manual testing against
    that exact URL earlier today, not a code problem. Left as-is
    rather than immediately retried, consistent with "run
    conservatively" — next week's cron (or a manual retry later) will
    pick it up.

**Status:** the design works, end to end, with real data, for the
first time. Remaining: ASISNZ's cache will need a retry at some
point; the "0 posts" connections are an open question, not a confirmed
bug; the stray `linkedin-fetch.toigroup.co.nz` DNS record (logged
earlier) is still outstanding.

## ASSET:asis 2026-10-22 -> Both LaunchAgents live; only login_linkedin.py and one DNS cleanup remain

**Built and loaded:**
  ~/Library/LaunchAgents/com.asisnz.linkedin-listener.plist
    runs py-asis/listener.py via .venv/bin/python3, RunAtLoad +
    KeepAlive, logs to launchd-stdout.log/launchd-stderr.log
  ~/Library/LaunchAgents/com.asisnz.linkedin-tunnel.plist
    runs `cloudflared tunnel --config ~/.cloudflared/py-asis.yml run`,
    same RunAtLoad + KeepAlive pattern, logs under ~/.cloudflared/

Loaded via `launchctl bootstrap gui/$(id -u) <plist>`. Both confirmed
running (`launchctl list | grep redwolf`), tunnel showing 4 registered
edge connections, listener bound on 127.0.0.1:8787.

**Verified end to end, persistently this time (not loose background
processes like the earlier test):** curled the real public hostname
with the correct `X-Listener-Secret` — got back
`{"slug":"TEST","error":"linkedin_storage_state.json missing — run
login_linkedin.py"}`, HTTP 200. Exactly the expected result with no
real session yet. This path now survives a reboot/logout; the earlier
E2E test did not.

**Status:** everything buildable or automatable from here is done.
Only two things remain, both outside anything scriptable:
  1. `login_linkedin.py`, run by hand — accepted as a recurring,
     infrequent cost (see prior entry's honesty correction on
     autonomy), not a blocker to everything else being ready
  2. Delete the stray `linkedin-fetch.toigroup.co.nz` CNAME from the
     Cloudflare dashboard (logged earlier, still outstanding — this
     API token has no DNS-write scope)
Once (1) is done, `fetch-linkedin.yml`'s `workflow_dispatch` can be
run for a real test with actual LinkedIn data — the first point since
this whole design started where that's actually true.

## ASSET:asis 2026-10-22 -> Dropped Cloudflare Access; honest note on what Plan B actually fixes (not full autonomy)

**Decision: Access is not required.** `listener.py`'s existing
`LISTENER_SHARED_SECRET` check (`X-Listener-Secret` header) is a
sufficient auth layer on its own — already built, already confirmed
working over the real tunnel (401 without it, 200 with it).
`fetch_linkedin_cache.py` already degrades gracefully if
`CF_ACCESS_CLIENT_ID`/`CF_ACCESS_CLIENT_SECRET` are unset (just skips
those headers) — no code changes needed to drop Access. Residual risk:
the hostname `redwolf.toigroup.co.nz` isn't truly secret (any TLS cert
Cloudflare issues for it is discoverable via public Certificate
Transparency logs), but without the 256-bit shared secret nothing can
be done with it — the same security shape as any bearer-token API over
TLS. This removes the entire Zero Trust/service-token setup from the
remaining steps; only 2 GitHub secrets are needed, not 4, and both are
already set.

**Honest correction — Plan B does not achieve "fully autonomous."**
Re-examined after being asked directly whether manually running
`login_linkedin.py` just reintroduces the same human-dependency problem
claude-in-chrome had. It's a fair challenge, and the straight answer is
no design here achieves zero-touch-forever: any approach depending on
an authenticated LinkedIn session needs re-auth eventually, including
a dedicated bot account. What Plan B actually improves is frequency and
reliability of that dependency, not its existence:
  - claude-in-chrome: human needed on essentially every run (bridge
    connection found to drop during any idle period, no reliable
    keepalive after several attempts logged in md-repo), AND fails
    silently (headless claude -p has no Chrome tools at all under
    API-key auth — no error, just nothing).
  - Playwright + saved session: human needed only when the session
    actually expires (unpredictable timing, but infrequent, not
    per-run), AND fails loudly — `browse_linkedin.py` explicitly
    returns `{"error": "session expired"}` instead of guessing or
    silently breaking.
The original plan's "fully autonomous — agent calls endpoint without
human present" framing (very first entry, before any revision) was
aspirational even then. The real claim for Plan B is: autonomous most
weeks, with an explicit signal instead of silent/unreliable failure
when it isn't — not autonomous forever.

**Status:** Access dropped from the design (not just deferred).
Remaining steps unchanged in substance, reduced in count:
  1. `login_linkedin.py`, run by hand — accepted as a recurring,
     infrequent cost, not a one-time setup step
  2. Set up both LaunchAgents (listener + cloudflared)
  3. Delete the stray `linkedin-fetch.toigroup.co.nz` CNAME

## ASSET:asis 2026-10-22 -> fetch-linkedin.yml built; everything automatable without Cloudflare Access is now done

**GitHub secrets added (2 of the 4):** `LISTENER_SHARED_SECRET` (the
real value from py-asis's `.env`) and `LINKEDIN_FETCH_URL`
(`https://redwolf.toigroup.co.nz/fetch`) — both addable without
Access, since they don't depend on it.

**Built:** `.github/workflows/fetch-linkedin.yml` (item 2 of the
original plan) — weekly cron (Sun 20:00 UTC) + `workflow_dispatch` for
manual runs, plus `.github/scripts/fetch_linkedin_cache.py`: reads
`CAN/TREE-2026Q3.json`'s `connections{}`, maps each to its fixed slug
(same table as the `fetch-linkedin` skill — keep both in sync if
connections{} ever changes), calls the listener once per connection
30s apart (stdlib `urllib`, no pip install needed), writes successes to
`CAN/TREE-<SLUG>-2026Q3.json`. A failed/unreachable connection is
logged and skipped, never fails the job.

**Bug caught before shipping:** `git add CAN/TREE-*-2026Q3.json` with
zero matches — the current actual state, since nothing is fetchable
yet — would have errored and failed the whole job. Guarded with
`nullglob` + an explicit empty check before committing.

**Confirmed blocked, not just assumed:** tried enabling Cloudflare
Access via the API directly (`PUT .../access/organizations`) — same
"Authentication error" as the earlier DNS-write attempts. This
account's API token has no Zero Trust/Access scope at all; this one
genuinely needs the dashboard (or a token with that scope), not just
more scripting.

**Status:** every piece buildable without touching Cloudflare's
dashboard or a real LinkedIn login is now done. What's left is
entirely on the user's side:
  1. Enable Access (dashboard) → create the Access application +
     service token for `redwolf.toigroup.co.nz` → gives
     `CF_ACCESS_CLIENT_ID`/`CF_ACCESS_CLIENT_SECRET`, the last 2
     GitHub secrets
  2. `login_linkedin.py`, run by hand — the real authenticated session
  3. Set up both LaunchAgents (listener + cloudflared) so the tunnel
     survives reboots instead of running as loose background processes
  4. Delete the stray `linkedin-fetch.toigroup.co.nz` CNAME (logged
     earlier, still outstanding)
  Once 1–3 are done, `workflow_dispatch` on `fetch-linkedin.yml` can
  be used to test the real, fully-automated path end to end.

## ASSET:asis 2026-10-22 -> Real E2E test over the public tunnel — full round trip confirmed, 4th GitHub secret needed

**What was done:** generated a real `LISTENER_SHARED_SECRET` (`openssl
rand -hex 32`) into py-asis's `.env` (gitignored — this is now the
real value, not a test throwaway). Started `listener.py` and
`cloudflared tunnel run` for `py-asis` live, briefly, then hit the
real public hostname `https://redwolf.toigroup.co.nz/fetch` from the
actual internet (not localhost):
  - no `X-Listener-Secret` header → 401 (confirmed)
  - correct header → 200 with
    `{"slug":"TEST","error":"linkedin_storage_state.json missing — run
    login_linkedin.py"}` — the full real chain: public hostname →
    Cloudflare edge → tunnel → `listener.py` → `browse_linkedin.py` →
    JSON back through the same path, working end to end.

**Mistake made and fixed during this test:** first run of `listener.py`
used the system Python (the venv-activation fallback was written as
`source ... || (python3 -m venv ... && source ...)` — activating inside
a `(...)` subshell doesn't affect the parent shell, so the `nohup
python3 listener.py` right after it still picked up the system
Python). Result: `browse_linkedin.py` crashed with `ModuleNotFoundError:
No module named 'playwright'`, which `listener.py` correctly reported
as HTTP 502 (Cloudflare substituted its own generic error page body for
that 502 — expected Cloudflare behavior, not a bug in our code).
Fixed by starting `listener.py` with `.venv/bin/python3` explicitly
rather than relying on shell activation; re-ran, got the correct result
above.

**New finding — a 4th GitHub secret is needed, not 3:** since
`LISTENER_SHARED_SECRET` is now set, every request to the real endpoint
must include a matching `X-Listener-Secret` header — including the
future `fetch-linkedin.yml` GitHub Action's requests. Prior entries only
listed `CF_ACCESS_CLIENT_ID`, `CF_ACCESS_CLIENT_SECRET`,
`LINKEDIN_FETCH_URL` as the GitHub secrets to add — a 4th,
`LISTENER_SHARED_SECRET` (same value as py-asis's local `.env`), is
also required so the Action can send that header.

**Shut down after the test:** killed both `listener.py` and the
`cloudflared tunnel run` process for `py-asis`. Confirmed down —
the hostname returned Cloudflare's 530 ("no origin reachable")
afterward. Not left running, since Access still isn't enabled on the
account.

**Status:** real E2E round trip CONFIRMED working (minus an actual
authenticated LinkedIn session — still untested, still needs
`login_linkedin.py` run by hand). `.env`'s `LISTENER_SHARED_SECRET` is
now the real production value. Still open: add it as `md-asis`'s
4th GitHub secret alongside the other three once the Action is built;
Cloudflare Access (blocked); the stray DNS record cleanup (prior
entry); `fetch-linkedin.yml` itself.

## ASSET:asis 2026-10-22 -> Cloudflare Tunnel created for py-asis; one stray DNS record needs manual cleanup

**Created:** tunnel `py-asis` (id `973ee4ee-8089-41f1-be79-d87102cba334`),
hostname `redwolf.toigroup.co.nz` routed to it via
`cloudflared tunnel route dns`. Local config at
`~/.cloudflared/py-asis.yml` (gitignored, not in either repo) points
that hostname at `http://127.0.0.1:8787` — where `listener.py` will
listen once it's running.

**Mistake made and partly cleaned up:** first created the route as
`linkedin-fetch.toigroup.co.nz` before being asked to use
`redwolf.toigroup.co.nz` instead. Routed the correct hostname
immediately after — both now point at the same tunnel. Attempted to
delete the stray `linkedin-fetch.toigroup.co.nz` CNAME via the
Cloudflare API: failed every attempt (DELETE and PUT both returned
"Authentication error") — the available `$CLOUDFLARE_API_TOKEN` can
read DNS records on this zone but not edit/delete them. `cloudflared`
itself has no DNS-record-removal subcommand (`tunnel delete` removes
the whole tunnel, not one DNS record, and would also kill the correct
hostname's route).

**Still needs manual cleanup:** delete the `linkedin-fetch.toigroup.co.nz`
CNAME from the Cloudflare dashboard (DNS → records for `toigroup.co.nz`),
or supply a token with DNS-edit scope on that zone. Harmless as-is —
nothing is live behind either hostname yet, and whatever ends up
gating this (Access, the shared secret) will cover both identically
until it's removed — but it shouldn't be left long-term.

**Status:** tunnel + correct DNS route DONE. Nothing running yet —
no `cloudflared tunnel run` process is live, so neither hostname is
actually reachable right now. Still open: the stray-record cleanup
above, Cloudflare Access (blocked — not enabled on the account),
and everything else already logged as PLANNED in prior entries.

## ASSET:asis 2026-10-22 -> Partial E2E test of py-asis: plumbing verified, real bug found + fixed

**What was tested, locally, on this machine, no Cloudflare/GitHub Action
involved:**
  1. `browse_linkedin.py`'s missing-session guard — correctly returns
     `{slug, error: "linkedin_storage_state.json missing..."}` with no
     session file present.
  2. `listener.py`'s full HTTP path — started it, curled `/fetch` with
     real query params: confirmed it shells out to `browse_linkedin.py`,
     parses its JSON, and returns it verbatim. Also confirmed 400 on
     missing params, 404 on an unknown path.
  3. The `LISTENER_SHARED_SECRET` auth gate — 401 with no header, 401
     with the wrong value, 200 with the correct one (a throwaway test
     value, never committed).
  4. Real navigation against a real, public LinkedIn page
     (linkedin.com/company/microsoft) using an anonymous/empty session —
     LinkedIn serves a public preview without login, so this exercised
     real extraction, not a mock.

**Bug found and fixed:** `followerCount` came back `0` on the first
real fetch. Investigation found the CSS-class selector was matching a
"People also viewed" sidebar card's follower count instead of
Microsoft's own — LinkedIn's classes here are generic utility classes
with no stable semantic hook, and the same "N followers" text repeats
on those cards further down the page. Fixed by taking the first "N
followers" match in the page's plain visible text instead of a CSS
selector — the company's own count is reliably in the header, before
any sidebar content. Re-verified: correct count came back
(29,344,015, matching the real live figure). `bio` extraction was
correct on the first try, no fix needed. `recentPosts` remains an
untested stub — not exercised by this test.

**Also found:** 3 rapid real requests to the same page triggered a
timeout on the 4th — concrete confirmation of the ASSET log's existing
"run conservatively, one fetch per connection" guidance; not just a
theoretical risk. Also: Homebrew's Python on this machine is
externally-managed and refuses global `pip install` — README and the
launchd plist template now use a venv (`.venv/bin/python3`) instead of
system python3.

**What this did NOT test — still needs you:** everything here ran
against an anonymous session (empty storage state), since creating a
real one requires `login_linkedin.py`'s interactive LinkedIn login
(including any 2FA), which only you can do. Untested: the real
authenticated-session path, the "session expired" detection logic
(never triggered — anonymous view never hit an authwall for this
public page), and whether `recentPosts` extraction works at all
(still a stub). Also untested: the actual Cloudflare Tunnel, Access,
and the fetch-linkedin.yml GitHub Action — none of those exist yet.

**Status:** local plumbing + one real selector bug CONFIRMED FIXED
(py-asis commits c8787f1, f854a7d). Still open, unchanged in kind
from prior entries: real authenticated-session test, recentPosts
extraction, Cloudflare Access (blocked — not enabled on the account),
tunnel creation, GitHub Action.

## ASSET:asis 2026-10-22 -> claude-in-chrome retired for real; py-asis now uses Playwright (supersedes commits 145504d/fd4291c below)

**Why this entry exists:** commits 145504d and fd4291c (below, from a
separate session) re-confirmed the `claude -p browse-linkedin skill →
chrome session` design in README.TXT and this log — written a few
minutes before the finding that kills that design was found. Per the
append-only rule those entries are left as-is; this entry documents
what actually changed and why.

**Finding (from a separate repo, md-repo's chrome/could/ASSET-2026Q3.md,
not this project):** two independent problems make claude-in-chrome
unworkable for an unattended weekly cron:
  1. Headless Claude Code invocations (`claude -p`) normally run on
     API-key auth, which silently disables Chrome integration — no
     error, just no `mcp__claude-in-chrome__*` tools available.
  2. Even with interactive OAuth, that repo's own operational history
     found no reliable automated keepalive after several attempts
     (PowerShell UI automation clicking the extension, WebSocket bridge
     interception, cron-agent tab access — all retired as non-viable).
     The extension's service worker goes idle and the bridge drops;
     reconnecting needs a human to type `/chrome` → Reconnect.

Both are fundamentally incompatible with "GitHub Action fires on a
cron, no one is present."

**What changed in py-asis (private, commit 5073f65):**
  removed:  .claude/skills/browse-linkedin/SKILL.md
  added:    browse_linkedin.py   — Playwright, headless Chromium,
              loads linkedin_storage_state.json (a saved, pre-
              authenticated session), same JSON contract as before
              (slug/companyName/url/fetchedAt/followerCount/bio/
              recentPosts, or {slug, error})
            login_linkedin.py   — run by hand to create/refresh that
              session file (visible browser, manual login incl. 2FA)
            requirements.txt    — playwright only; kept pure Python,
              no Node/Puppeteer, matching why this repo is named
              py-asis and not ts-redwolf
  listener.py now shells out to browse_linkedin.py instead of
  `claude -p` — no claude CLI dependency on the mac mini at all for
  this piece anymore.

**What changed here in md-asis:** README.TXT step 1a's "How the
cache is built" block updated to say `browse_linkedin.py (Playwright,
saved LinkedIn session)` instead of `claude -p browse-linkedin skill →
chrome session`. Step 1a itself (reading CAN/TREE-<SLUG>-2026Q3.json)
is unchanged — this only affects how py-asis produces those files.

**Note on 145504d/fd4291c's "not claude-in-chrome" framing:** that
framing was correct about step 1a specifically (md-asis's
fetch-linkedin skill only ever read cache files, never called
claude-in-chrome itself) but didn't carry through to py-asis's write
side, which — per those same commits' own diagrams — still was `claude
-p` + a chrome session. This entry closes that gap for real.

**Status:** py-asis side DONE (pushed). Still open: verify the
placeholder CSS selectors in browse_linkedin.py against a real logged-in
LinkedIn page; the mac-mini setup steps (Playwright install, session
login, tunnel, LaunchAgents) and the fetch-linkedin.yml GitHub Action
remain PLANNED, same as logged previously.

## ASSET:asis 2026-10-22 -> Step 1a plan confirmed and documented in README.TXT (commit 145504d)

**Confirmed:** Step 1a does NOT use claude-in-chrome from this session and does NOT
fetch LinkedIn directly. Claude only reads pre-cached TREE-<SLUG> JSON files.

**Full chain (as documented in README.TXT step 1a):**
  GitHub Action (weekly cron, fetch-linkedin.yml)
    → Cloudflare Tunnel → py-asis/listener.py on mac mini
        → runs: claude -p browse-linkedin skill (ts-redwolf/.claude/skills/)
            → chrome session on mac mini (authenticated LinkedIn)
                → returns JSON { recentPosts[], bio, followerCount } per slug
    → Action commits CAN/TREE-<SLUG>-2026Q3.json to md-asis repo

  Claude step 1a (md-asis)
    → reads CAN/TREE-<SLUG>-2026Q3.json (same pattern as TREE-2026Q3.json)
    → informs 1b subtype selection
    → fallback: web search per slug while cache is not yet live

**Cache file naming (CAN/, one per connection):**
  TREE-ASISNZ-2026Q3.json, TREE-NZSA-2026Q3.json, TREE-ASIS-2026Q3.json,
  TREE-NZPOLICE-2026Q3.json, TREE-JOHNSON-2026Q3.json, TREE-GALLAGHER-2026Q3.json,
  TREE-INNERRANGE-2026Q3.json, TREE-BOSCH-2026Q3.json, TREE-ICT-2026Q3.json,
  TREE-JACQUES-2026Q3.json

**Still to build:**
  - fetch-linkedin.yml GitHub Action (md-asis)
  - CF_ACCESS_CLIENT_ID / CF_ACCESS_CLIENT_SECRET / LINKEDIN_FETCH_URL GitHub secrets
  - fetch-linkedin Claude skill (.claude/skills/fetch-linkedin/SKILL.md)
  - mac mini setup: cloudflared tunnel, LaunchAgents, .env

**Status:** PLANNED — README updated, architecture confirmed, nothing built yet.

## ASSET:asis 2026-10-22 -> Org transfer completed (asisnz); ts-redwolf renamed to py-asis

**Org transfer:** both repos moved from the jayreck996 personal account
into the `asisnz` org (confirmed existing org, admin role active) via
`POST /repos/{owner}/{repo}/transfer`:
  jayreck996/md-asis  -> asisnz/md-asis  (public)
  jayreck996/ts-redwolf  -> asisnz/ts-redwolf  (private)

Verified after transfer: GitHub Pages rebuilt automatically at the new
host — https://asisnz.github.io/md-asis/ (replaces
jayreck996.github.io/md-asis/, which does NOT redirect — different
hostname, per the risk flag logged earlier). Existing Actions secret
(MD_ASISNZ) carried over intact. Local clones' remotes updated to the
new org URLs on this machine.

**Rename:** asisnz/ts-redwolf -> asisnz/py-asis (via
`gh repo rename`), since the repo is pure Python (listener.py, stdlib
only) rather than TypeScript — matches the existing `py-*` naming used
elsewhere (py-quiz, py-test, py-portfolio) better than `ts-*`. Local
folder renamed to match; self-references inside the repo's own files
(listener.py, README.md, cloudflared/launchd templates) updated to the
new name, and README's link to md-asis fixed from the old
jayreck996 owner to asisnz.

**Known stale references not touched (append-only):** this file's own
earlier entries above still say "ts-redwolf" and link to
github.com/jayreck996/ts-redwolf — historical, left as-is per this
repo's append-only log rule. Same applies to the 44
raw.githubusercontent.com/asisnz/md-asis/... links already in
this file and the 12 in COULD/TABLE-2026Q3.csv — not yet verified
whether they still resolve post-transfer.

**Status:** org transfer + rename DONE. Still open: confirm whether the
old raw.githubusercontent.com/jayreck996 media links still resolve;
send the client the new Pages URL; the mac-mini tunnel/GitHub Action
work flagged in the prior entries remains PLANNED.

## ASSET:asis 2026-10-22 -> Risk flags: moving md-asis + ts-redwolf into a new 'redwolf' GitHub org

**Proposal under discussion:** create a new GitHub org `redwolf` (name
confirmed available) and transfer both `md-asis` and `ts-redwolf` into
it, so the client-facing repo and its private write-side pair share an
org instead of sitting under the personal account.

**Cannot be automated end-to-end:** GitHub's API has no "create
organization" endpoint, and `gh` has no `repo transfer` subcommand — org
creation is a manual step at https://github.com/organizations/new; the
repo transfer itself can be scripted afterward via the REST API
(`POST /repos/{owner}/{repo}/transfer`).

**Risk flags:**
  1. GitHub Pages URL changes host, not just path:
     jayreck996.github.io/md-asis/ -> redwolf.github.io/md-asis/.
     This is the client's review site (STEP 4). The old URL will NOT
     keep working via redirect — different hostname entirely. The client
     would need the new link sent to them.
  2. 44 hardcoded raw.githubusercontent.com/asisnz/md-asis/...
     links already exist in this file's history, plus 12 in
     COULD/TABLE-2026Q3.csv (week-43 media URLs etc). GitHub generally
     redirects github.com/<old-owner>/<repo> paths after a transfer, and
     raw.githubusercontent.com usually follows the same mapping, but this
     is not a documented permanent guarantee. Per this repo's append-only
     log rule, historical entries containing these links cannot be
     rewritten even if the links go stale later.
  3. Local clones on this machine point at jayreck996/... remotes for
     both repos — mechanical fix after a transfer, not a blocker.
  4. GitHub Actions secrets stay attached to a repo through a transfer,
     so md-asis's planned CF_ACCESS_* / LINKEDIN_FETCH_URL secrets
     (once added) are unaffected.
  5. ts-redwolf is private with no public links — no Pages/raw-link risk
     for that repo specifically.

**Status:** FLAGGED for decision — org not yet created, no transfer has
happened. Item 1 (Pages URL) is the real cost; the rest is mechanical.

## ASSET:asis 2026-10-22 -> Claude skill plan: items 1–2 revised, split into new private repo ts-redwolf

**Revision:** Item 1 (macnimi server) is no longer a bespoke Node.js +
Puppeteer endpoint. It's now a headless Claude Code invocation
(`claude -p`) that runs a new `browse-linkedin` skill using claude-in-chrome
against the mac mini's own, already-authenticated LinkedIn Chrome session —
a real browsing session instead of a scripted scraper. Item 2 (the trigger
side) is unchanged in shape: still a GitHub Action calling the mac mini and
committing the result, just now calling this new listener instead of a raw
Puppeteer endpoint.

**Why split into a second repo:** `md-asis` is public. The browsing
method (headless Claude Code + claude-in-chrome + an authenticated session)
and the mac-mini infra (listener, tunnel config) shouldn't be public, even
though they contain no secrets themselves. Created
[`ts-redwolf`](https://github.com/jayreck996/ts-redwolf) (private) as the
write-side pair to `md-asis`'s read side — matching the existing
`md-<client>` / `ts-<client>` convention already used elsewhere (e.g.
`md-recruitment-dev` / `ts-recruitment-dev`).

**Revised architecture:**
  GitHub Action on md-asis (cron — weekly)
    → HTTPS GET <LINKEDIN_FETCH_URL>/fetch?slug=<SLUG>&url=<linkedin-url>
        via Cloudflare Tunnel + Access (service token, GH secret)
    → ts-redwolf/listener.py (127.0.0.1:8787 on the mac mini)
        checks LISTENER_SHARED_SECRET, serializes requests (one at a time)
        runs: claude -p "<browse-linkedin invocation>" (cwd=ts-redwolf)
    → ts-redwolf/.claude/skills/browse-linkedin/
        claude-in-chrome opens one tab on the company's LinkedIn page,
        reads bio/followerCount/recentPosts, closes the tab,
        prints one JSON object (or {slug, error} on failure) to stdout
    → listener.py returns that JSON → Action commits
      CAN/TREE-<SLUG>-2026Q3.json to md-asis (unchanged from before)

  md-asis's fetch-linkedin skill (STEP 1a) still just reads those
  committed cache files — unchanged, never talks to ts-redwolf or the mac
  mini directly.

**Built in ts-redwolf (private, pushed):**
  listener.py — stdlib-only, binds 127.0.0.1, one request at a time
  .claude/skills/browse-linkedin/SKILL.md — one page, one connection per run
  cloudflared.config.yml.template, com.asisnz.linkedin-listener.plist.template,
    .env.example — setup templates only, no real secrets committed
  README.md — wiring diagram + one-time mac-mini setup steps

**Still open (needs the mac mini / Cloudflare dashboard, not git):**
  1. cloudflared tunnel login/create, DNS route, Access application +
     service token
  2. Fill in the real .env and cloudflared.config.yml locally (gitignored)
  3. Load both as LaunchAgents (listener + cloudflared)
  4. Confirm Chrome stays logged into LinkedIn with claude-in-chrome enabled
  5. Add CF_ACCESS_CLIENT_ID / CF_ACCESS_CLIENT_SECRET / LINKEDIN_FETCH_URL
     as md-asis GitHub secrets, then build
     .github/workflows/fetch-linkedin.yml

**Risk:** unchanged from the original note below — LinkedIn ToS prohibits
scraping. A real authenticated session is the same kind of risk as the
original Puppeteer design, just a different shape; keep the cron weekly,
one fetch per connection, no retries that widen scope.

**Status:** ts-redwolf scaffolded and pushed (items 1, 3 of the original
plan, revised). Item 2 (GitHub Action) and the mac-mini-side setup above
still PLANNED.

## ASSET:asis 2026-10-22 -> Claude skill plan: items 3–4 built (fetch-linkedin skill + README)

**Built:** `.claude/skills/fetch-linkedin/SKILL.md` — implements item 3 of the
Option B design below. During STEP 1a it reads the cached
`CAN/TREE-<SLUG>-2026Q3.json` snapshots instead of calling LinkedIn directly,
maps all 10 connections to their fixed slugs (ASISNZ, NZSA, ASIS, NZPOLICE,
JOHNSON, GALLAGHER, INNERRANGE, BOSCH, ICT, JACQUES), flags MISSING (no cache
file) or STALE (`fetchedAt` >7 days) connections instead of blocking the
batch, and summarizes recent activity per connection to inform 1b. Read-only:
never calls LinkedIn, never writes the cache files.

**Also built (item 4):** README.TXT step 1a now references the skill and the
`TREE-<SLUG>` cache files instead of the old direct-`fetch()` instructions.

**Still open:** item 1 (macnimi server endpoint) and item 2
(`.github/workflows/fetch-linkedin.yml`) — blocked on the macnimi server's
address/auth, which only the client has.

**Status:** items 3–4 BUILT. Items 1–2 still PLANNED; no cache files exist
yet, so the fetch-linkedin skill will report every connection as MISSING
until the Action starts writing them.

## ASSET:asis 2026-10-22 -> Claude skill plan: LinkedIn fetch via macnimi server + GitHub Action

**Plan:** Replace step 1a fetch() — which LinkedIn blocks unauthenticated — with a weekly
GitHub Action that calls a macnimi server running Puppeteer, caches results as TREE-<SLUG>
files in CAN/, and Claude reads those files during step 1a.

**Architecture (Option B — scheduled cache):**
  GitHub Action (cron — weekly, before batch day)
    → calls macnimi server: GET /linkedin?slug=<slug> for each connection
        → macnimi runs Puppeteer with authenticated LinkedIn session
            → returns JSON { recentPosts[], bio, followerCount }
    → Action commits CAN/TREE-<SLUG>-2026Q3.json to repo

  Claude (step 1a)
    → reads CAN/TREE-<SLUG>-2026Q3.json (same pattern as CAN/TREE-2026Q3.json)
    → extracts recent posts/announcements per connection
    → informs 1b subtype selection

**Cache files (CAN/, per connection):**
  TREE-ASISNZ-2026Q3.json
  TREE-NZSA-2026Q3.json
  TREE-ASIS-2026Q3.json
  TREE-NZPOLICE-2026Q3.json
  TREE-JOHNSON-2026Q3.json
  TREE-GALLAGHER-2026Q3.json
  TREE-INNERRANGE-2026Q3.json
  TREE-BOSCH-2026Q3.json
  TREE-ICT-2026Q3.json
  TREE-JACQUES-2026Q3.json

**To build:**
  1. macnimi server endpoint — Node.js + Puppeteer
     GET /linkedin?slug=<slug> → JSON { recentPosts[], bio, followerCount }
     Must be publicly reachable by GitHub Actions (Cloudflare tunnel or similar)
  2. GitHub Action — .github/workflows/fetch-linkedin.yml
     Cron schedule, loops all slugs from TREE-2026Q3.json connections{},
     commits each TREE-<SLUG>-2026Q3.json result to CAN/
  3. Claude skill — .claude/skills/fetch-linkedin/SKILL.md
     Instructs agent to read CAN/TREE-*-2026Q3.json files in step 1a
  4. README update — step 1a references the skill and TREE-<SLUG> files

**Risk:** LinkedIn ToS prohibits scraping; run conservatively (one fetch per
connection per week, human-like delays) to reduce detection risk.

**Status:** PLANNED — not yet built.

## ASSET:asis 2026-10-22 16:20 -> Week 43 media generated for fresh batch (commit 64f00b7)

**Why:** 64f00b7 replaced all six week 43 posts again; five media URLs pointed to placeholders that did not exist (404). Media now lives in COULD/media/2026Q3/ after the folder rename (6c99c42). None of the 20 Oct week 43 graphics fit the new posts; removed (still in git history): post-007-survey-diagnostic, post-008-nzsa-departing-staff, post-009-nzsa-membership, post-011-gov-case-study-carousel (+ slides 1–5), post-012-protect-the-experience, post-010-PLACEHOLDER.md.

**Media (all png, 1080x1350):**
- post-007 IQP Inspections — compliance schedule → IQP inspection → Form 12A → Building WOF, access-controlled doors as SS 3/2: https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-007-iqp-inspections.png
- post-008 AI in Surveillance — traditional CCTV vs AI analytics split, plus "what it doesn't do": https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-008-cctv-vs-ai.png
- post-009 Expert Opinion — detect / delay / respond layers with examples; delay must outlast response: https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-009-detect-delay-respond.png
- post-010 Career Growth — technician → senior technician → team lead → lead consultant; training, NZSA qualifications, mentoring: https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-010-career-pathway.png
- post-011 NZSA Accreditation — member vs accredited, plus tender question: https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-011-nzsa-accreditation-tender.png
- post-012 Security Awareness Month — tailgating, propped doors, unmonitored visitors, outdated credentials, each with a fix; comment CTA: https://raw.githubusercontent.com/asisnz/md-asis/main/COULD/media/2026Q3/post-012-awareness-month-fixes.png

**Sources checked:** building.govt.nz (IQP, Form 12A, annual BWOF; most specified systems inspected at least yearly); council SS 3/2 access controlled doors forms; security.org.nz accreditation process and membership requirements.

**Verify before publishing:**
- post-007: copy says ASIS New Zealand "is registered to carry out IQP inspections across Wellington and Auckland" — confirm IQP registration with each council. Official term is "independent qualified person" (copy says "Independently Qualified Person").
- post-011: COPY FIX — "annual self-audit assessed by independent auditors" is the membership requirement; accreditation is an independent onsite audit against NZSA Codes of Practice (5-year term, annual declaration). VERIFY "ASIS New Zealand has held NZSA accreditation since our founding".
- post-010: verify "several of our senior consultants and team leads started as installation technicians" and the NZSA qualifications claim. Graphic shows a generic pathway, no names or timeframes.
- post-008: copy says ASIS New Zealand installs AI analytics for mid-market clients — confirm.
- post-009: "20 years in the industry" — still unverified.

**Note:** week 41 media (post-013 to post-018) remains in COULD/media/2026Q3/ unreferenced.

## ASSET:asis 2026-10-20 17:30 -> Week 43 media generated for fresh subtopics (commit 5b9220f)

**Why:** 5b9220f replaced all six week 43 posts with new subtopics and reset media URLs to placeholders (five did not exist). None of the previous week 43 graphics fit; they were removed (still in git history): post-007-noc-alarm-timeline, post-008-ai-analytics, post-009-five-gaps, post-011-late-night-response, post-012-security-awareness-month.

**Media (SHOULD/media/2026Q3/, 1080x1350):**
- post-007 Protective Security Surveys — 3-stage diagram (site assessment, gap analysis, recommendations) + compliance vs diagnostic: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-007-survey-diagnostic.png
- post-008 NZ Security Industry Standards — NZSA position statement on confidential information and departing staff: employer and departing-staff obligations, access to revoke at final working time: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-008-nzsa-departing-staff.png
- post-009 NZSA Membership — trust signals card + questions to ask: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-009-nzsa-membership.png
- post-011 Government & Critical Infrastructure — 5-slide carousel PDF (challenge, scope/stage/deliver, result, CTA): https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-011-gov-case-study-carousel.pdf (+ post-011-slide-1..5.png)
- post-012 Industry News Commentary — "Security should protect the experience, not just the assets" with friction vs enabler: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-012-protect-the-experience.png
- post-010 Company Culture — media-type jpg, needs a real team photo. Placeholder updated.

**Sources checked:** NZSA position statement "Confidential Information and Departing Staff" (security.org.nz/wp-content/uploads/2026/10/NZSA_Professional-Standard.pdf) — advisory "expected professional standard", not binding. NZSA membership requirements (security.org.nz, why choose an NZSA member).

**Verify before publishing:**
- post-012: the quote attributed to "NZSA Board Member Mark Knoff-Thomas" at the "Profit Protection Future Forum" could not be found online; his public role found is Newmarket Business Association. The graphic deliberately does NOT name him or present a direct quote. Confirm the quote, his title and the event (link a source) before using it in the copy.
- post-011: this presents a real government project. Confirm the facts (full access control + CCTV upgrade, staged, live operations) and get client approval; government/critical infrastructure clients often restrict publicity. Graphic names no agency or building.
- post-008: copy says NZSA "released guidance on staff transitions" — accurate; it is a position statement (advisory), not a regulation.
- post-009: copy matches NZSA membership requirements. Confirm ASIS New Zealand is a member.
- post-010: verify culture claims; get consent for any photo.

## ASSET:asis 2026-10-20 17:05 -> Week 43 media re-evaluated after batch regeneration (commit 9173fbf)

**Relinked:** 9173fbf reset week 43 media URLs to PLACEHOLDER.md files; only post-010's exists, the other five returned 404. All six now point to real files.

**Kept (copy reworded, same substance):**
- post-007 https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-007-noc-alarm-timeline.png — 5-step alarm-to-resolution timeline still matches.
- post-008 https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-008-ai-analytics.png — "AI detection capabilities" infographic still matches.
- post-011 https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-011-late-night-response.png — incident timeline still matches.

**Updated:** post-009 https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-009-five-gaps.png — headline now "The 5 security gaps we see most in Wellington businesses" to match the new title; same five gaps and fixes. Removed post-009-five-mistakes.png.

**Replaced:** post-012 is now Campaigns & Seasonal / Security Awareness Month (was Hot Take). New graphic https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-012-security-awareness-month.png — "Don't forget the physical side": propped doors, visitor books no one checks, access never reviewed after staff departures. Removed post-012-hot-take.png.

**Still BLOCKED:** post-010 — media-type now jpg; needs a real staff/team photo and technician quotes with consent. Verify "over six years" average tenure.

**Verify:** post-011 title now says "A Client's Account" — the post presents a client's first-hand account, so written client approval is required (graphic carries no client quote). post-009 "20+ years" and post-007 "Wellington and Auckland" still unverified.

**Note:** week 41 rows were dropped in 05d2801; post-013 to post-018 media files remain in SHOULD/media/2026Q3/ unreferenced.

## ASSET:asis 2026-10-13 23:10 -> Week 41 media re-evaluated after batch regeneration (commit f552bd3)

**Relinked:** f552bd3 reset all six week 41 media URLs to non-existent placeholders (404). All six relinked.

**Unchanged (content identical to d2ad2a5):** post-013, post-015, post-016, post-017, post-018 — existing graphics kept.

**Replaced:** post-014 is now Cybersecurity Convergence (was Physical Security Threats). New graphic https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-014-cyber-physical.png — IT/physical Venn with the overlap (building automation, access control, IP cameras, intercoms), three attack vectors from the copy (outdated building automation, phished credentials, physical entry to network breach) and a four-point unified approach. Removed post-014-physical-threats.png.

**Verify:** post-014 copy calls the convergence gap "the fastest-growing risk for NZ organisations" — unsourced; soften or cite. Open items for post-016 and post-017 from the 23:00 entry still apply.

## ASSET:asis 2026-10-13 23:00 -> Week 41 media updated for LinkedIn-research rewrite (commit 50491bb)

**Media URLs unchanged** (same filenames, all 18 table links return 200). Files updated in place:
- post-013 access-control.png — capabilities now match copy: real-time door monitoring, tailgating alerts, audit trail, instant lockdown (replaced time-based permissions and CCTV-linked events). No Gallagher branding on the graphic.
- post-014 physical-threats.png — tag changed to "Cybersecurity Awareness Month".
- post-016 industry-involvement.png — four items: NZSA working groups, position statements, technician training, industry events and awards (NZSA awards).
- post-017 nzsa-accreditation.png — added note that members and accredited members are expected to uphold NZSA professional standards (codes of conduct, position statements incl. confidential information and departing staff, Sept 2026).
- post-018 did-you-know.png — assumptions 4 and 5 now match copy: visitor management stops at the front desk; no security audit since the last fit-out.
- post-015 unchanged.

**Source checked:** security.org.nz/position-statements — "Prof Standards: Confidential Info & Departing Staff - Sept 2026" exists.

**Still open:** post-017 copy still attributes the membership requirements (annual self-audit reviewed by independent auditors) to accreditation; "current licences across every technician" is not stated by NZSA for accreditation. post-016: verify ASIS New Zealand's actual working-group, position-statement and awards involvement. post-018: verify "two decades in the field".

## ASSET:asis 2026-10-13 22:45 -> Week 41 media regenerated for redone batch (commit d41340c)

**Why:** d41340c replaced all six week 41 posts (new subtopics, titles, descriptions, media briefs) and reset media URLs to non-existent placeholders. None of the previous week 41 graphics fit; all six replaced and the old files removed (still in git history).

**Media (SHOULD/media/2026Q3/, 1080x1350, built to each row's media brief):**
- post-013 access control: credential types, door zones, 4 capabilities — https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-013-access-control.png
- post-014 physical threats: tailgating, credential sharing, insider risk, social engineering, each with a control — https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-014-physical-threats.png
- post-015 pre-consultation checklist (6 items) + 3 questions to ask — https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-015-briefing-checklist.png
- post-016 industry involvement: industry groups, technician training, industry events — https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-016-industry-involvement.png
- post-017 NZSA member vs accredited comparison — https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-017-nzsa-accreditation.png
- post-018 Did You Know: 5 assumptions, "usually false" — https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-018-did-you-know.png

**Source checked:** security.org.nz accreditation process — accreditation is an independent onsite audit against NZSA Codes of Practice, 5-year term, annual declaration of no material change; re-audit on material change. Membership (separate) = vetting incl. licence, min $1m liability cover, annual self-audit reviewed by independent auditors, Code of Ethical Conduct.

**Status / verify:**
- post-013 READY. Confirm the credential types and CCTV integration match systems ASIS New Zealand actually installs.
- post-014 READY.
- post-015 READY.
- post-016 READY as a typographic card. VERIFY ASIS New Zealand's actual involvement (NZSA working groups, training, events) — the graphic states it in general terms. Real event or training photos would be stronger.
- post-017 READY. COPY FIX: the description says accreditation requires "an annual self-audit reviewed by independent auditors" — that is the membership requirement. Accreditation is an independent onsite audit, 5-year term, annual declaration. "current licences across every technician" is not stated on the accreditation page. VERIFY ASIS New Zealand is NZSA accredited (not only a member) before posting.
- post-018 READY. Overlaps post-009 (week 43: untested systems, CCTV angles) — consider spacing them apart. Copy says "two decades in the field"; verify.

## ASSET:asis 2026-10-13 22:20 -> Week 41 media re-evaluated after persona re-angle (commit 754ccf9)

**Relinked:** commit 754ccf9 reset all week 41 media URLs to PLACEHOLDER.md files that do not exist (404). All six now point to real media again.

**Kept (content unchanged):** post-013 https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-013-security-survey.png · post-015 https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-015-nzsa-membership.png · post-017 https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-017-quality-process.png (media text says "ISO 9001" but the graphic carries no ISO badge; certification still unverified).

**Updated:** post-014 https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-014-psr-framework.png — headline "The PSR framework in practice", checklist relabelled "Have this ready before any audit, tender or review". Earlier copy issues (critical infrastructure mandate, "what has been updated") are resolved by the new description.

**Replaced:**
- post-016 https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-016-project-delivery.png — values card no longer fit the new angle; new graphic shows four client commitments (one point of contact, milestones up front, proactive updates, formal close-out). Removed post-016-asis-new-zealand-values.png.
- post-018 https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-018-year-end-decisions.png — three decisions: IT/physical convergence, IQP paperwork for access-controlled doors (specified system SS 3/2, building WOF), footage retention policy (Privacy Act, principle 9). Removed post-018-three-trends.png.

**Sources checked:** building.govt.nz (IQP inspection, Form 12A, annual BWoF); council SS 3/2 access controlled doors forms; privacy.org.nz principle 9 (retention).

**Verify:** post-016 commitments must match how ASIS New Zealand actually runs projects. post-018 copy says AI cameras create "new liability" — keep it framed as a privacy obligation, not legal advice.

## ASSET:asis 2026-10-13 21:55 -> Week 41 media generated (post-013 to post-018)

**Media (SHOULD/media/2026Q3/, same brand system, 1080x1350):**
- post-013 survey 3-stage diagram: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-013-security-survey.png
- post-014 PSR framework checklist: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-014-psr-framework.png
- post-015 NZSA trust signals card: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-015-nzsa-membership.png
- post-016 RED WOLF values card: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-016-asis-new-zealand-values.png
- post-017 quality process explainer: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-017-quality-process.png
- post-018 three trends commentary: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-018-three-trends.png

**Sources checked:** PSR via ncsc.govt.nz (4 areas: governance, personnel, information, physical; mandatory for public service agencies; annual self-assessment against 20 mandatory requirements). NZSA via security.org.nz (vetting incl. licence check; min $1m public and product liability; annual self-audit reviewed by independent auditors; Code of Ethical Conduct; complaints and disciplinary procedure).

**Status:**
- post-013 READY. Generic survey process; confirm it matches how ASIS New Zealand runs surveys.
- post-014 READY. Copy fix: description says PSR sets obligations for "critical infrastructure providers" — the Cabinet mandate covers public service agencies (plus NZDF, Police, NZSIS, PCO), not private critical infrastructure. Also "what has been updated" — no 2026 PSR update found; remove or cite one.
- post-015 READY. Graphic does not claim ASIS New Zealand is a member. Copy fix: "not self-certification ... independently verified" overstates it — the annual audit is a self-audit reviewed by independent auditors. Verify ASIS New Zealand's NZSA membership before posting.
- post-016 READY as branded values card (no photo). Values from COULD/README.TXT.
- post-017 READY. No ISO badge or certification claim on the graphic. VERIFY ASIS New Zealand holds ISO 9001 before posting — the post copy states it and it remains unverified.
- post-018 READY. Trends are ASIS New Zealand's commentary, not cited data.

**Table:** media and media URL updated for post-013 to post-018 (placeholders were never created; links were 404 before this).

## ASSET:asis 2026-10-13 -> Week 41 content batch generated (post-013 to post-018)

**Posts added to SHOULD/TABLE-2026Q3.csv:**

| Item | Category | Type | Subtopic | Value | Score | Status |
|------|----------|------|----------|-------|-------|--------|
| post-013 | SERVICES | Consulting & Design | Protective Security Surveys | Ownership | 7 | BLOCKED: needs survey process diagram |
| post-014 | INDUSTRY | Regulation & Compliance | NZ Security Industry Standards | Learn | 8 | BLOCKED: needs PSR checklist graphic |
| post-015 | AUTHORITY | Accreditations & Partnerships | NZSA Membership | Excellence | 8 | BLOCKED: needs NZSA trust signals card |
| post-016 | PEOPLE | Culture & Values | Company Culture | We Before Me | 7 | BLOCKED: needs team culture photo or values card |
| post-017 | TRUST | Compliance & Certifications | ISO 9001 | Reliable | 8 | BLOCKED: needs ISO 9001 explainer card |
| post-018 | ENGAGEMENT | Community & Reposts | Industry News Commentary | Future Focused | 7 | BLOCKED: needs 3-trend commentary graphic |

**Persona alignment:** All posts written to the Security Manager persona (MUST/README.TXT) — compliance, quality, reliability, and process themes throughout.

**Tags used:** @ASIS New Zealand on all posts. @New Zealand Security Association on post-014, 015, 018.

**Verify before publishing:**
- post-014: confirm PSR framework details are current for 2026
- post-015: confirm NZSA membership is active and licence details are accurate
- post-017: confirm ISO 9001 certification is current before publishing

## ASSET:asis 2026-10-13 -> Structural updates: feedback-comment column, tree feedback counts, week number correction

**CSV — SHOULD/TABLE-2026Q3.csv:**
- Added `feedback-comment` column (last column, after `feedback`)
- Week numbers corrected to ISO week: batch 1 (post-001–006) 27 → 42 (Oct 12–18), batch 2 (post-007–012) 28 → 43 (Oct 19–25)

**Tree — MUST/TREE-2026Q3.json:**
- Added `"feedback": {"win": N, "tie": 0, "lost": N, "comments": []}` to all 54 subtypes
- Seeded with week 42 actuals: CCTV win:1, Emerging Risks lost:1, Team Certifications win:1, Polls win:1

**Workflow — .github/workflows/update-feedback.yml:**
- Now writes `feedback-comment` to CSV and appends comment to tree subtype `comments[]` on each dispatch

**Status:** READY — no media impact, structural only.

## ASSET:asis 2026-10-13 18:22 -> Week 28 adjustment check: media unchanged

**Change since media was generated:** post-008 partner tags changed from Bosch to Gallagher Security + Integrated Control Technology (commit 7f25753). No other week 28 content changed.

**Media impact:** none. post-008-ai-analytics.png carries no partner names or logos, so it stays valid. The earlier "confirm the Bosch tag" note is superseded.

**Verify:** post-008 is about AI video analytics. Per MUST/README.TXT rule 5, confirm Gallagher and ICT are directly relevant (e.g. video analytics integrated with their access control platforms), otherwise tag only ASIS New Zealand.

## ASSET:asis 2026-10-13 18:05 -> Week 28 media generated (post-007, 008, 009, 011, 012)

**Media (SHOULD/media/2026Q3/, same brand system as week 27, 1080x1350):**
- post-007 alarm-to-resolution timeline: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-007-noc-alarm-timeline.png
- post-008 AI detection event types: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-008-ai-analytics.png
- post-009 five mistakes tip card: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-009-five-mistakes.png
- post-011 late-night incident timeline: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-011-late-night-response.png
- post-012 hot take opinion graphic: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-012-hot-take.png

**Status:**
- post-007 READY as a graphic instead of a NOC photo. No response times or site counts on the graphic; verify "hundreds of sites" and "Wellington and Auckland" in post copy.
- post-008 READY. No Bosch branding on the graphic; confirm the Bosch tag fits the partnership.
- post-009 READY. Mistakes 4 and 5 (untested systems, unmanaged contractor access) added to complete the five. Verify "20+ years" in post copy.
- post-010 BLOCKED: needs staff photo and real technician quotes with consent; verify "6+ years" average tenure. Placeholder file added so its link no longer 404s.
- post-011 READY as an incident timeline, deliberately without a client quote. Add a real quote only with the client's written approval; confirm the 11pm CBD incident details.
- post-012 READY. Opinion only, no figures.

**Table:** media and media URL updated for post-007/008/009/011/012.

## ASSET:asis 2026-10-13 -> Week 28 content batch generated (post-007 to post-012)

**Branch:** `main`

**Posts added to SHOULD/TABLE-2026Q3.csv:**

| Item | Category | Type | Subtopic | Score | Status |
|------|----------|------|----------|-------|--------|
| post-007 | SERVICES | Monitoring & Response | Network Operations Centre | 7 | BLOCKED: needs NOC photo |
| post-008 | INDUSTRY | Technology Trends | AI in Surveillance | 8 | BLOCKED: needs AI detection infographic |
| post-009 | AUTHORITY | Thought Leadership | Expert Opinion | 8 | BLOCKED: needs 5-point tip card graphic |
| post-010 | PEOPLE | Team Spotlight | Staff Profiles | 7 | BLOCKED: needs staff/team photo |
| post-011 | TRUST | Testimonials & Social Proof | Client Quotes | 8 | BLOCKED: needs client quote graphic; verify client approval for story |
| post-012 | ENGAGEMENT | Interactive | Questions & Debates | 7 | BLOCKED: needs branded opinion graphic |

**Subtypes deliberately varied from week 27** (no repeat of CCTV, Emerging Risks, Awards, Behind the Scenes, Case Study/Commercial, Polls).

**Verify before publishing:**
- post-008: confirm Bosch tag is appropriate (check partnership scope)
- post-009: "20+ years" — ASIS New Zealand founded 2005, so 21 years in 2026; adjust copy if needed
- post-011: client story must be anonymised or have written approval before posting

## ASSET:asis 2026-10-13 -> Research branch: LinkedIn connections, score, week column

**Branch:** `research`

**Changes:**
- `MUST/TREE-2026Q3.json` — added `connections` block: own (ASIS New Zealand), associations (NZSA, ASIS International, NZ Police), partners (Johnson Controls, Gallagher Security, Inner Range ANZ, Bosch, ICT, Jacques Technologies)
- `SHOULD/TABLE-2026Q3.csv` — added `score` column (1–10, content priority) and `week` column (first column, batch key); all 6 posts set to week 27; pattern: 6 posts per week, one per category

**Score logic:** post-003 AUTHORITY/Awards=10 (strongest observed post type), post-005 TRUST/Case Study=9, post-002/004 INDUSTRY+PEOPLE=8, post-001/006 SERVICES+ENGAGEMENT=7

## ASSET:asis 2026-10-13 14:16 -> Q3 media generated, audited, repo cleaned up

**Brand:** Real logo (`logo.jpg`) and its colours: red `#EF1925`, shield grey `#C8C9CB`, ink `#211F20`. Font Inter. Canvas 1080x1350 portrait.

**Media (SHOULD/media/2026Q3/, all links public, HTTP 200):**
- post-002 drone threat infographic: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-002-drone-threats.png
- post-005 case study carousel, 5-slide PDF: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-005-case-study-carousel.pdf (downloads; preview at https://github.com/asisnz/md-asis/blob/main/SHOULD/media/2026Q3/post-005-case-study-carousel.pdf)
- post-005 slides: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-005-slide-1.png … post-005-slide-5.png
- post-006 poll teaser: https://raw.githubusercontent.com/asisnz/md-asis/main/SHOULD/media/2026Q3/post-006-poll.png

**Table:** `media URL` in SHOULD/TABLE-2026Q3.csv points to the files above for post-002/005/006. post-001/003/004 still point to PLACEHOLDER.md.

**Status:**
- post-002 READY. Verify: jamming or bringing down a drone is illegal for private businesses in NZ.
- post-005 READY. Verify slide 2 wording against client facts; client approval needed.
- post-006 READY as teaser only (LinkedIn native polls can't carry an image). Options A–D fit the 30-char limit. Verify "We ask this every year" in post copy.
- post-001 BLOCKED: needs approved, anonymised before/after install photos.
- post-003 BLOCKED: needs award-night photo; verify NZSA award details and names.
- post-004 BLOCKED: needs install footage/photos with staff consent.

**Unverified, kept off all media:** redwolf.net.nz, ISO 9001, NZSA accreditation, Auckland office.

**Open question:** whether Johnson Controls brand/approval rules apply (ASIS New Zealand recruitment runs via Johnson Controls).

**Posting:** LinkedIn doesn't attach media by URL; download and upload each file when creating the post.

**Repo cleanup:** Removed earlier SVG drafts (COULD/media/), the old scaffold (lowercase could/ must/ should/ would/, root ASSET/ISSUE 2026Q3 + 2026Q4 logs, README.md). ts-web still targets could/ and may recreate it until repointed.

## ASSET:asis 2026-10-13 -> Repo concept: LinkedIn post content generator for ASIS New Zealand

**Purpose:** This repo is dedicated to LinkedIn post content generation for ASIS New Zealand.

**LinkedIn:** https://www.linkedin.com/company/asis-new-zealand/home/

**Scope:** All content, assets, tables, trees, and logs in this repo serve as structured source material for drafting, scheduling, and publishing LinkedIn posts on behalf of the ASIS New Zealand brand.
