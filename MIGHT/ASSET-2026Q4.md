ASSET LOG
INSTRUCTION FOR AI MODEL:

ALWAYS ADD NEW ASSET ENTRIES AT THE TOP, DIRECTLY BELOW THIS HEADER.

NEVER DELETE OR EDIT PREVIOUS ASSET ENTRIES.

REQUIRED FORMAT FOR EACH ASSET ENTRY:

## ASSET:{NAME OF ENVIRONMENT} {YYYY-MM-DD HH:MM} → {CONTENT}

####### <!-- ANCHOR MARKER - ADD ALL NEW ASSET ENTRIES DIRECTLY BELOW THIS LINE, NEVER DELETE OR EDIT PREVIOUS ASSET ENTRIES-->

## ASSET:asis 2026-11-02 13:15 → Laptop (WSL) public key authorized on Mac mini; repos pulled; password login still ON

**Pulled:** `md-redwolf` (fast-forward to `fc3ab67`) and `md-asis` (fast-forward to `db31240`, picking up the laptop's 14:00 WSL entry). No conflicts.

**Authorized key:** appended the `laptop-wsl` ed25519 public key from the 14:00 WSL entry to `~/.ssh/authorized_keys` on the Mac mini, after the user confirmed it was theirs. File has exactly one key, chmod 600. Fingerprint `SHA256:1yg2oy/ZLQbCPM47gIDDa889TRvP1rKUwqOs+c72uoM`. Mac mini login user is `jayreck`.

**Not yet verified:** key login from the laptop (private key lives only on the laptop). Needs `cloudflared` installed in WSL (`sudo dpkg -i /tmp/cloudflared.deb`, interactive), then `ssh macmini`.

**Still to do:**
- Confirm `ssh macmini` works key-only from WSL.
- After that, disable SSH password and keyboard-interactive login on the Mac mini (admin required). Not before, to avoid lockout.
- Optional: `cloudflared` upgrade 2026.3.0 → 2026.10.7 (restarts all four tunnels briefly); Cloudflare Access policy on `ssh.toigroup.co.nz` / `asis.toigroup.co.nz`; trigger the `fetch-linkedin` workflow for the first real end-to-end run.


## ASSET:asis 2026-11-02 14:00 → SSH laptop (WSL) side complete — public key ready to authorize on Mac mini

**Done on laptop (WSL):**
- SSH keypair generated: `~/.ssh/id_ed25519` (ed25519, comment `laptop-wsl`), permissions 600/644.
- `~/.ssh/config` written (permissions 600):
```
Host macmini
  HostName ssh.toigroup.co.nz
  User jayreck
  IdentityFile ~/.ssh/id_ed25519
  ProxyCommand cloudflared access ssh --hostname %h
```
- `cloudflared-linux-amd64.deb` downloaded to `/tmp/cloudflared.deb` — needs `! sudo dpkg -i /tmp/cloudflared.deb` (interactive terminal required).

**Public key to add to Mac mini `~/.ssh/authorized_keys`:**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILmPBQjMToMVZaWWZuJ/nzdjYEpqVv1ubmi84CISd1K7 laptop-wsl
```
On the Mac mini: `echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILmPBQjMToMVZaWWZuJ/nzdjYEpqVv1ubmi84CISd1K7 laptop-wsl" >> ~/.ssh/authorized_keys`

**To connect once cloudflared is installed in WSL:**
```bash
! sudo dpkg -i /tmp/cloudflared.deb
ssh macmini
```

**Note:** SSH is on the `toigroup` tunnel (`ssh.toigroup.co.nz`), not `py-asis` — as recorded in the 12:45 Q4 entry. The Q3 ASSET log's py-asis SSH ingress plan is superseded by this.

## ASSET:asis 2026-11-02 13:10 → ASIS pipeline live end to end (LinkedIn session, GitHub secrets, py-asis pushed); SSH remote ready on Mac mini but no key authorized yet

**LinkedIn session:** ran `login_linkedin.py` in `py-asis` (interactive, ASIS New Zealand account). Saved `linkedin_storage_state.json` (gitignored, chmod 600, `li_at` cookie present, 47 cookies). Test fetch through the public tunnel (`https://asis.toigroup.co.nz/fetch`, `X-Listener-Secret` header) returned HTTP 200: ASISNZ, 138 followers, bio, recent posts. One fetch only, per the one-per-week guidance.

**py-asis repo:** port change 8787 → 8788 committed and pushed to `asisnz/py-asis` main (`5ef8632`), so the repo now matches the running listener.

**GitHub secrets set in `asisnz/md-asis`** (pattern copied from `redwolfnz/md-redwolf`): `LINKEDIN_FETCH_URL` = `https://asis.toigroup.co.nz/fetch`, `GENERATE_CONTENT_URL` = `https://asis.toigroup.co.nz`, `LISTENER_SHARED_SECRET` (from `py-asis/.env`, piped straight to `gh secret set`, never printed). Existing `MD_ASIS` unchanged. `CF_ACCESS_CLIENT_ID` / `CF_ACCESS_CLIENT_SECRET` deliberately not set: md-redwolf runs without them (unset secrets expand to empty strings in Actions) and the shared secret is the auth layer. This corrects the earlier statement that generate-content would fail without them. `fetch-linkedin` workflow not yet triggered.

**Naming / tunnel health:** no LaunchAgents renamed; `com.redwolf.*` keep their names. `com.redwolf.linkedin-tunnel` exit status 1 is a stale value, process healthy.

**SSH remote status:** tunnel live (`ssh.toigroup.co.nz` on the `toigroup` tunnel, see 12:45 entry). Created empty `~/.ssh/authorized_keys` (chmod 600) on the Mac mini; pubkey auth enabled by default. No laptop key authorized yet, so login via the tunnel still returns "Permission denied". Password and keyboard-interactive login still ON. The Mac mini's own `id_ed25519.pub` (`jayreck-macmini`) was NOT authorized (it is its outbound key).

**Still to do:**
- Laptop (WSL): install `cloudflared`; add `macmini` entry to `~/.ssh/config` (HostName `ssh.toigroup.co.nz`, User `jayreck`, ProxyCommand `cloudflared access ssh --hostname %h`); `ssh-keygen -t ed25519 -C "laptop-wsl"`; authorize via `ssh-copy-id -i ~/.ssh/id_ed25519.pub macmini` or by giving the public key to append to `authorized_keys`; test `ssh macmini`.
- After the key test works: disable SSH password login (needs admin; not before, to avoid lockout).
- Optional: `cloudflared` upgrade 2026.3.0 → 2026.10.7 (restarts all four tunnels briefly); Cloudflare Access policy on `ssh.toigroup.co.nz` / `asis.toigroup.co.nz`.
- Trigger `fetch-linkedin` workflow as the first real end-to-end run.


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
