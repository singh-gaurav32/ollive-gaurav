# Oracle Cloud VM Provisioning Checklist — Ollive Deployment

Working checklist for taking the Oracle Cloud "Always Free" account from "created" to a live `k3s` cluster running Ollive. Expands the README's condensed walkthrough into trackable steps. Check items off as you go; fill in the blanks (IP, hostname, etc.) so this doc becomes the record of what was actually done, not just what was planned.

Design decisions behind these choices: `aidlc-docs/construction/unit-06-packaging-deployment/infrastructure-design/`.

**Who does what**: the OCI console steps (A-D) need to happen in your browser, under your account — I can't act on your Oracle Cloud account directly. I'll give exact settings for each screen; you click through and report back (or paste values) so we can keep going. Once you have SSH access to the VM (step F onward), I can drive those commands directly if you'd like — just say so when we get there.

---

## A. SSH key pair — done

- [x] Checked existing keys — found `~/.ssh/termux_ed25519`, but it's scoped to a specific Termux host in `~/.ssh/config`, so generated a dedicated key instead
- [x] Generated: `~/.ssh/ollive_oracle_ed25519` (+ `.pub`)
- [x] Public key, ready to paste during instance creation:
  ```
  ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBP92HQGfmTyolfgG0yWa/UXfYLrXuHyXu2ht2Fdy9Ze ollive-oracle-vm
  ```

---

## B. Create the Compute Instance — done, deviated from plan

**What actually happened** (recorded here since it changes later steps):
1. First attempt: shape/image selection defaulted to OCI's other Always Free shape, `VM.Standard.E2.1.Micro` (1 OCPU/1GB, x86) instead of Ampere A1 — too small to run this stack. Instance created at `161.118.184.11`, **not used, should be terminated** as cleanup (see Status section).
2. Second attempt: correctly selected Ampere A1.Flex (ARM) + Ubuntu 22.04, but hit `Out of host capacity for shape VM.Standard.A1.Flex in AD-1` — a genuine, common Always-Free ARM capacity constraint in `ap-mumbai-1`, not specific to this account.
3. Third attempt: created **`VM.Standard.E2.4`** instead (4 OCPU / 32GB, **x86_64**, NOT part of Always Free — bills against the 30-day/$300 trial credit). Verified via the instance's own metadata endpoint. **Running at `144.24.101.70`.** A $5/month budget alert was set up on the root compartment as a safety net before proceeding.

**Consequence for later steps**: our images are multi-arch (`python:3.12-slim`, `node:20-alpine`, `nginx:alpine`, `pgvector/pgvector:pg16` all publish amd64 builds), so x86 changes nothing about the app itself. Given this VM is intentionally short-lived (trial, user plans to tear down within about a week), we're **skipping the reserved static IP in step C** — the ephemeral IP won't change as long as the instance keeps running continuously, and DuckDNS's `A` record is a one-field update if it ever does.

- [x] Instance running at **`144.24.101.70`**, `ap-mumbai-1-AD-1`, `VM.Standard.E2.4` (4 OCPU/32GB, x86_64)
- [x] $5/month OCI Budget alert created on root compartment (belt-and-suspenders alongside the trial's own no-auto-charge policy)
- [ ] **Cleanup**: terminate the unused `161.118.184.11` (`VM.Standard.E2.1.Micro`) instance whenever convenient — not blocking, just tidy

---

## C. Reserve a static public IP — skipped

**Decision**: skipped, not forgotten. This VM is intentionally short-lived (trial instance, plan to tear down within about a week per the user). The ephemeral IP (`144.24.101.70`) won't change as long as the instance keeps running continuously, and reserving a static IP adds a step with no real benefit for a demo this short — if the IP ever does change (e.g. after a stop/start cycle), DuckDNS's `A` record is a one-field fix in step E.

- [x] Using ephemeral IP directly: **`144.24.101.70`**

---

## D. Open the firewall (80, 443, 22 only)

OCI Console → **Networking → Virtual Cloud Networks** → your VCN → **Security Lists** (or Network Security Groups if you're using one) → the subnet's default security list → **Add Ingress Rules**

- [ ] Rule 1: Source `0.0.0.0/0`, TCP, destination port **22** (likely already present by default)
- [ ] Rule 2: Source `0.0.0.0/0`, TCP, destination port **80**
- [ ] Rule 3: Source `0.0.0.0/0`, TCP, destination port **443**
- [ ] Confirm no other inbound rules are open beyond these three (check for an overly-permissive default rule and tighten it if present)

**Also on the VM itself**: Ubuntu's `ufw`/`iptables` may independently block traffic even after the OCI-level security list allows it — we'll confirm this in step F once SSH'd in (Ubuntu 22.04 on OCI images often ship `iptables` rules restricting to the security-list-allowed ports already, but worth double-checking with `sudo iptables -L` if 80/443 don't respond later).

---

## E. DuckDNS

- [x] Signed up, created subdomain (first choice `gaurav` was already taken by another DuckDNS user — subdomains are global/first-come-first-served)
- [x] Using **`gaurav-ollive.duckdns.org`**, set to `144.24.101.70`
- [x] Propagation confirmed: `dig +short gaurav-ollive.duckdns.org` → `144.24.101.70`
- [x] Pre-filled the real hostname into `k8s/ingress.yaml` (both `tls.hosts` and `rules.host`) and the real contact email (`singh.gaurav.id@gmail.com`) into `k8s/cluster-issuer.yaml`, committed to `main` — nothing left to hand-edit for these two files in step I

---

## F. SSH in, install k3s

- [x] `ssh -i ~/.ssh/ollive_oracle_ed25519 ubuntu@144.24.101.70` — confirmed working (used earlier to check instance metadata)
- [x] Installed k3s `v1.36.3+k3s1` — note: this step was initially skipped by mistake (jumped straight to image building after DuckDNS), caught when applying manifests failed with `k3s: command not found`; installed at that point instead
- [x] Confirmed: `sudo k3s kubectl get nodes` → one node, `Ready`, control-plane
- [x] Traefik + local-path storage class present by default, no separate install needed

---

## G. Install cert-manager — done

- [x] Applied `cert-manager.yaml`
- [x] `rollout status deploy/cert-manager` → successfully rolled out

---

## H. Build and push images — done, with a further deviation: built ON the VM after all

**Decision change #1** (from NFR Requirements' original "no registry, build on VM"): switched to **GHCR**, reasoning as originally noted below.

**Decision change #2** (discovered while executing #1): local build machine is Apple Silicon (arm64), VM is x86_64 — a plain local `docker build` produces the wrong architecture. Proper cross-compilation needs `buildx` + QEMU emulation, which isn't set up with this machine's Colima-backed Docker and wasn't worth configuring for a one-off. Pragmatic fix: installed Docker **on the VM** after all (native x86_64, no emulation needed), built both images there, and pushed to GHCR from the VM instead of from the Mac. Net result is the same as originally intended (GHCR-hosted images, no manual `ctr import`) — just the build step happens on the VM, not locally. Future rebuilds: either repeat this (SSH, `git pull`, rebuild, push) or invest in local `buildx`/QEMU setup if it becomes a frequent need.

- [x] Both `docker login ghcr.io` sessions done **in the user's own terminal** (local Mac, and separately on the VM as `root` via `sudo docker login`) — kept out of this conversation
- [x] Built both images on the VM: `ghcr.io/singh-gaurav32/ollive-api:latest`, `ghcr.io/singh-gaurav32/ollive-frontend:latest`
- [x] Pushed both to GHCR
- [x] Package visibility set to **Public** for both (GitHub profile → Packages → each package → Package settings → Change visibility)
- [x] Pushed local commits (GHCR image refs, DuckDNS host, Let's Encrypt email) to `origin/main`, VM's clone updated via `git pull` (now at `5cdbfd1`)

---

## I. Fill in secrets and the real hostname

- [ ] `cp k8s/secrets.yaml.example k8s/secrets.yaml`
- [ ] Edit `k8s/secrets.yaml` — set `GEMINI_API_KEY`, choose a real `POSTGRES_PASSWORD`, update `DATABASE_URL` to match
- [ ] Edit `k8s/ingress.yaml` — replace `YOUR-SUBDOMAIN.duckdns.org` with the real hostname from step E (two places: `tls.hosts` and `rules.host`)
- [ ] Edit `k8s/cluster-issuer.yaml` — replace `your-email@example.com` with a real email (Let's Encrypt uses this for expiry notices, not shown publicly)

---

## J. Apply the manifests

- [x] `sudo k3s kubectl apply -f k8s/namespace.yaml`
- [x] `sudo k3s kubectl apply -f k8s/` (applies everything else)

---

## K. Verify — done, live

- [x] All pods reached `Running` (api had 2 early restarts racing Postgres startup, self-healed)
- [x] Certificate `READY: True` — real Let's Encrypt cert issued via HTTP-01 through Traefik
- [x] `https://gaurav-ollive.duckdns.org` loads the login page over real HTTPS
- [x] Logged in, sent chat messages, checked the dashboard — all working end-to-end against the live deployment

**Post-launch fixes found via live use** (not blocking the deployment itself, found and fixed after K passed):
1. `GEMINI_API_KEY` had a typo on first entry → fixed via `k8s/secrets.yaml` + `kubectl apply` + `rollout restart deployment/api`
2. Google retired `gemini-2.0-flash`, then `gemini-2.5-flash` was also gated for new API keys → settled on `gemini-3-flash-preview` after confirming with a local test script (`backend/`, real API, no cluster round-trip) — much faster feedback loop than redeploying to debug
3. Dashboard's bucket column showed only the start time, not the full range — small UI fix, verified locally then redeployed

All fixes followed: local test/verify → commit → push → rebuild on VM → push to GHCR → `rollout restart`. Live site now shows real successful Gemini responses (1925ms and 4868ms latencies visible in the dashboard).

---

## Status

- **Started**: 2026-08-16
- **Current step**: none — deployment complete and live, in post-launch stabilization
- **Live URL**: https://gaurav-ollive.duckdns.org
- **Instance**: `144.24.101.70`, `VM.Standard.E2.4` (4 OCPU/32GB x86, trial billing, $5 budget alert active), `ap-mumbai-1-AD-1`
- **Registry**: GHCR (`ghcr.io/singh-gaurav32/ollive-{api,frontend}:latest`), public, built natively on the VM (see Step H for why local cross-compilation was abandoned) and pushed from there
- **Cleanup pending**: terminate unused `161.118.184.11` (wrong-shape first attempt) — not urgent, no cost, just tidiness
- **Blockers**: none
