ASSET LOG
INSTRUCTION FOR AI MODEL:

ALWAYS ADD NEW ASSET ENTRIES AT THE TOP, DIRECTLY BELOW THIS HEADER.

NEVER DELETE OR EDIT PREVIOUS ASSET ENTRIES.

REQUIRED FORMAT FOR EACH ASSET ENTRY:

## ASSET:{NAME OF ENVIRONMENT} {YYYY-MM-DD HH:MM} → {CONTENT}

####### <!-- ANCHOR MARKER - ADD ALL NEW ASSET ENTRIES DIRECTLY BELOW THIS LINE, NEVER DELETE OR EDIT PREVIOUS ASSET ENTRIES-->

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
