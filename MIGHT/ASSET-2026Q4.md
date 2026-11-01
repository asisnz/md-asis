ASSET LOG
INSTRUCTION FOR AI MODEL:

ALWAYS ADD NEW ASSET ENTRIES AT THE TOP, DIRECTLY BELOW THIS HEADER.

NEVER DELETE OR EDIT PREVIOUS ASSET ENTRIES.

REQUIRED FORMAT FOR EACH ASSET ENTRY:

## ASSET:{NAME OF ENVIRONMENT} {YYYY-MM-DD HH:MM} → {CONTENT}

####### <!-- ANCHOR MARKER - ADD ALL NEW ASSET ENTRIES DIRECTLY BELOW THIS LINE, NEVER DELETE OR EDIT PREVIOUS ASSET ENTRIES-->

## ASSET:asis 2026-11-02 13:00 → ASIS split onto its own `py-asis` Cloudflare tunnel + listener on port 8788 (supersedes the "not done" listener-move line in the 12:45 entry below)

**Done on the Mac mini:**
- Cloned `asisnz/py-asis` to `~/Documents/GitHub/py-asis`; created `.venv` and installed `requirements.txt` (Playwright browsers already cached from Red Wolf). Generated `py-asis/.env` with `LISTENER_SHARED_SECRET` (gitignored, mode 600).
- Listener port changed 8787 → 8788 in `py-asis` (`listener.py` `LISTEN_PORT`, README, cloudflared template) because Red Wolf's listener already uses 8787. **Uncommitted in py-asis at time of writing.**
- Created tunnel `py-asis` (id `875158ed-73ca-4b43-b7d5-f914977b0c5c`, credentials `~/.cloudflared/875158ed-….json`). Config `~/.cloudflared/py-asis.yml`: `asis.toigroup.co.nz` → `http://127.0.0.1:8788`, else 404.
- DNS: `cloudflared tunnel route dns py-asis asis.toigroup.co.nz`.
- LaunchAgents added and loaded: `com.asisnz.linkedin-listener` (py-asis venv python → `listener.py`) and `com.asisnz.linkedin-tunnel` (cloudflared with `py-asis.yml`; logs `~/.cloudflared/py-asis-tunnel-{stdout,stderr}.log`).
- Verified: both agents running (exit 0), tunnel has 2 edge connections, `127.0.0.1:8788` and `https://asis.toigroup.co.nz/` both answer 404 on `/` (same as Red Wolf). Red Wolf tunnel/listener untouched.
- SSH deliberately left on the `toigroup` tunnel (`ssh.toigroup.co.nz`), not moved to `py-asis` as the py-asis cloudflared template suggested, to avoid a duplicate DNS record.

**Naming:** the Red Wolf agents keep their `com.redwolf.*` names; `com.redwolf.linkedin-tunnel` listing exit status 1 is a stale last-exit value, the process is healthy.

**Still to do:**
- Run `login_linkedin.py` in `py-asis` (interactive ASIS LinkedIn login; no saved session yet, so fetches will fail until done).
- GitHub secrets in `asisnz/md-asis`: `LINKEDIN_FETCH_URL` = `https://asis.toigroup.co.nz/fetch`, `GENERATE_CONTENT_URL` = `https://asis.toigroup.co.nz`, plus the shared secret from `py-asis/.env` as the workflow expects.
- Optional: Cloudflare Access service-token policy on `asis.toigroup.co.nz` (currently protected by the shared secret only).
- Commit and push the py-asis port-change edits.


## ASSET:asis 2026-11-02 12:45 → Mac mini SSH via Cloudflare Tunnel live on `toigroup` tunnel (supersedes the PLANNED py-asis entries in ASSET-2026Q3)

**Done on the Mac mini (Jays-Mac-mini, user `jayreck`):**
- No `py-asis` tunnel exists on this machine (tunnels: py-redwolf, toifood, toigroup), so SSH was added to the existing `toigroup` tunnel instead of the one planned in ASSET-2026Q3.
- `~/.cloudflared/toigroup.yml`: added ingress rule `hostname: ssh.toigroup.co.nz` → `service: ssh://localhost:22` (first rule; validated with `cloudflared tunnel ingress validate`).
- DNS: `cloudflared tunnel route dns toigroup ssh.toigroup.co.nz` created the CNAME.
- Restarted LaunchAgent `com.cloudflared.toigroup` (`launchctl kickstart -k`); 4 tunnel connections registered.
- Remote Login was already ON (port 22 open).
- Tested from the Mac mini itself via `ProxyCommand cloudflared access ssh --hostname ssh.toigroup.co.nz`: reached sshd, got `Permission denied (publickey,password,keyboard-interactive)` because no key is authorized yet. Tunnel path confirmed working.

**Laptop (WSL) steps, not yet done:** install `cloudflared`; add to `~/.ssh/config`:
```
Host macmini
  HostName ssh.toigroup.co.nz
  User jayreck
  ProxyCommand cloudflared access ssh --hostname %h
```
then `ssh-keygen -t ed25519 -C "laptop-wsl"`, `ssh-copy-id -i ~/.ssh/id_ed25519.pub macmini`, `ssh macmini`.

**Open items:** no Cloudflare Access policy on `ssh.toigroup.co.nz` (protected by SSH auth only); disable SSH password login once the key works. The asis LinkedIn listener tunnel move and GitHub secrets (`LINKEDIN_FETCH_URL`, `GENERATE_CONTENT_URL`) from ASSET-2026Q3 remain not done.

**Rollback:** previous config backed up at `/private/tmp/claude-501/-Users-jayreck-Documents-GitHub/2930eed7-689e-48cf-989d-58df85e74c51/scratchpad/toigroup.yml.bak`.
