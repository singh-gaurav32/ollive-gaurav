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
- [ ] Install k3s: `curl -sfL https://get.k3s.io | sh -`
- [ ] Confirm it's running: `sudo k3s kubectl get nodes` (should show one `Ready` node)
- [ ] This also installs **Traefik** (ingress) and the **local-path** storage class — no separate install needed for either

---

## G. Install cert-manager

- [ ] `sudo k3s kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml`
- [ ] Wait for it: `sudo k3s kubectl -n cert-manager rollout status deploy/cert-manager`

---

## H. Build and push images — revised mid-deployment: GHCR instead of build-on-VM

**Decision change from NFR Requirements' original "no registry, build on VM"**: since Docker already works locally and a GitHub repo (`github.com/singh-gaurav32/ollive-gaurav`) is already in play, pushing to **GHCR (GitHub Container Registry)** is now simpler than installing Docker on the VM and manually re-building/re-importing on every update. The VM only needs k3s/containerd (already there) — no Docker install on the VM at all. `k8s/api-deployment.yaml` and `k8s/frontend-deployment.yaml` updated to `image: ghcr.io/singh-gaurav32/ollive-api:latest` / `ollive-frontend:latest`, `imagePullPolicy: Always` (was `Never`).

- [ ] Generate a GitHub PAT (`write:packages` scope) and run `docker login ghcr.io` **in your own terminal** (kept out of this conversation on purpose)
- [ ] Build and push, from the local repo (not the VM):
  ```bash
  docker build -t ghcr.io/singh-gaurav32/ollive-api:latest ./backend
  docker push ghcr.io/singh-gaurav32/ollive-api:latest
  docker build -t ghcr.io/singh-gaurav32/ollive-frontend:latest --build-arg VITE_API_BASE_URL="" ./frontend
  docker push ghcr.io/singh-gaurav32/ollive-frontend:latest
  ```
- [ ] **First push only**: GHCR packages default to **private** even from a public repo — go to your GitHub profile → **Packages** → select `ollive-api` (and `ollive-frontend`) → **Package settings → Danger Zone → Change visibility → Public** (needed so the VM can pull without an `imagePullSecret`; confirm this is acceptable — no secrets are baked into the image, those come in via the k8s `Secret`, but the image contents/code become publicly downloadable)
- [ ] On the VM: just clone the repo for the `k8s/` manifests and README — no build needed there:
  ```bash
  sudo apt update && sudo apt install -y git
  git clone https://github.com/singh-gaurav32/ollive-gaurav.git && cd ollive-gaurav
  ```

---

## I. Fill in secrets and the real hostname

- [ ] `cp k8s/secrets.yaml.example k8s/secrets.yaml`
- [ ] Edit `k8s/secrets.yaml` — set `GEMINI_API_KEY`, choose a real `POSTGRES_PASSWORD`, update `DATABASE_URL` to match
- [ ] Edit `k8s/ingress.yaml` — replace `YOUR-SUBDOMAIN.duckdns.org` with the real hostname from step E (two places: `tls.hosts` and `rules.host`)
- [ ] Edit `k8s/cluster-issuer.yaml` — replace `your-email@example.com` with a real email (Let's Encrypt uses this for expiry notices, not shown publicly)

---

## J. Apply the manifests

- [ ] `sudo k3s kubectl apply -f k8s/namespace.yaml`
- [ ] `sudo k3s kubectl apply -f k8s/` (applies everything else)

---

## K. Verify

- [ ] `sudo k3s kubectl -n ollive get pods` — all should reach `Running`
- [ ] `sudo k3s kubectl -n ollive get certificate` — wait for `READY=True` (Let's Encrypt issuance can take a minute or two)
- [ ] Visit `https://YOUR-SUBDOMAIN.duckdns.org` in a browser — should load the login page over real HTTPS
- [ ] Log in as one of the seeded demo users, send a chat message, check the dashboard — same checks as the local verification, now against the live deployment

---

## Status

- **Started**: 2026-08-16
- **Current step**: D (open the firewall) — SSH (step F's connectivity) already confirmed working while troubleshooting step B
- **Instance**: `144.24.101.70`, `VM.Standard.E2.4` (4 OCPU/32GB x86, trial billing, $5 budget alert active), `ap-mumbai-1-AD-1`
- **Cleanup pending**: terminate unused `161.118.184.11` (wrong-shape first attempt)
- **Blockers**: none currently — Ampere A1 capacity issue was worked around by switching to a paid trial x86 shape
