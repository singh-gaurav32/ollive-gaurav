# Oracle Cloud VM Provisioning Checklist — Ollive Deployment

Working checklist for taking the Oracle Cloud "Always Free" account from "created" to a live `k3s` cluster running Ollive. Expands the README's condensed walkthrough into trackable steps. Check items off as you go; fill in the blanks (IP, hostname, etc.) so this doc becomes the record of what was actually done, not just what was planned.

Design decisions behind these choices: `aidlc-docs/construction/unit-06-packaging-deployment/infrastructure-design/`.

**Who does what**: the OCI console steps (A-D) need to happen in your browser, under your account — I can't act on your Oracle Cloud account directly. I'll give exact settings for each screen; you click through and report back (or paste values) so we can keep going. Once you have SSH access to the VM (step F onward), I can drive those commands directly if you'd like — just say so when we get there.

---

## A. SSH key pair

- [ ] Check if you already have one: `ls ~/.ssh/id_ed25519.pub` (or `id_rsa.pub`)
- [ ] If not, generate one: `ssh-keygen -t ed25519 -C "ollive-oracle-vm"`
- [ ] Have the **public** key contents ready to paste during instance creation (`cat ~/.ssh/id_ed25519.pub`)

---

## B. Create the Compute Instance

OCI Console → **Compute → Instances → Create Instance**

- [ ] **Name**: `ollive-vm` (or your preference)
- [ ] **Compartment**: your root/default compartment is fine for a single demo VM
- [ ] **Placement / Availability Domain**: default is fine
- [ ] **Image**: **Ubuntu 22.04** — click "Change Image", filter to Canonical Ubuntu, select 22.04, confirm it's the **aarch64/ARM** variant
- [ ] **Shape**: click "Change Shape" → **Ampere** → **VM.Standard.A1.Flex** → set **4 OCPUs / 24 GB memory** (the full Always Free allocation)
- [ ] **Boot volume**: expand "Boot volume" → set size to **50 GB**
- [ ] **Networking**: use the default VCN/subnet (or create one if this is a fresh account with none yet) — leave "Assign a public IPv4 address" checked for now (we'll swap it for a reserved one in step C)
- [ ] **SSH keys**: paste your public key from step A
- [ ] Click **Create**, wait for the instance state to become **Running** (a few minutes)
- [ ] Note the instance's **ephemeral public IP** shown on the instance detail page: `________________`

**If instance creation fails with "Out of host capacity"**: this is a known, common Always-Free Ampere A1 constraint in some regions/AD combinations — not specific to this setup. Try a different Availability Domain in the same region first; if it keeps failing, that's the trigger for the pre-agreed fallback (Hetzner/DigitalOcean VPS, same `k3s` steps below apply unchanged).

---

## C. Reserve a static public IP

OCI Console → **Networking → IP Management → Reserved Public IPs → Create Reserved Public IP**

- [ ] Create a new reserved IP in the same region
- [ ] Note the reserved IP: `________________`
- [ ] Attach it to the VM: go to the instance's **VNIC** → **IPv4 Addresses** → edit the public IP → switch from "Ephemeral" to your new **Reserved IP**
- [ ] Confirm you can still reach the instance at the new IP (`ping` or just note it — SSH check comes in step F)

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

- [ ] Sign up / log in at [duckdns.org](https://www.duckdns.org) (GitHub/Google/etc. login, no separate password)
- [ ] Create a subdomain, e.g. `ollive.duckdns.org` — record the exact one chosen: `________________`
- [ ] Set its IP to the **reserved static IP** from step C
- [ ] Verify propagation: `dig +short YOUR-SUBDOMAIN.duckdns.org` should return the reserved IP (may take a few minutes)

---

## F. SSH in, install k3s

- [ ] `ssh ubuntu@<reserved-ip>` (default user for Ubuntu OCI images is `ubuntu`) — confirm you're in
- [ ] Install k3s: `curl -sfL https://get.k3s.io | sh -`
- [ ] Confirm it's running: `sudo k3s kubectl get nodes` (should show one `Ready` node)
- [ ] This also installs **Traefik** (ingress) and the **local-path** storage class — no separate install needed for either

---

## G. Install cert-manager

- [ ] `sudo k3s kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml`
- [ ] Wait for it: `sudo k3s kubectl -n cert-manager rollout status deploy/cert-manager`

---

## H. Get the code onto the VM and build images

- [ ] Install git/docker on the VM if not already present (Ubuntu 22.04 cloud images usually need `sudo apt update && sudo apt install -y git docker.io` and `sudo usermod -aG docker ubuntu` — logout/login after the `usermod`)
- [ ] Clone the repo: `git clone <your-repo-url> && cd ollive`
- [ ] Build the images:
  ```bash
  docker build -t ollive-api:latest ./backend
  docker build -t ollive-frontend:latest --build-arg VITE_API_BASE_URL="" ./frontend
  ```
- [ ] Import into k3s's containerd (separate store from Docker's):
  ```bash
  docker save ollive-api:latest | sudo k3s ctr images import -
  docker save ollive-frontend:latest | sudo k3s ctr images import -
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

- **Started**: _(date)_
- **Current step**: A
- **Blockers**: none yet
