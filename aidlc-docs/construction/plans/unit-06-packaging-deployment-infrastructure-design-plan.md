# Unit 6 — Packaging & Deployment — Infrastructure Design Plan

## Context
NFR Design fixed the *patterns* (Traefik, cert-manager, PVC, k8s Secret). This stage maps those to concrete Oracle Cloud resources: region, VM shape, OS image, storage sizing, and confirms monitoring scope.

## Steps
- [x] Collect answers to the questions below
- [x] Resolve any ambiguous answers with follow-ups
- [x] Generate `infrastructure-design.md` and `deployment-architecture.md`

## Questions

### Deployment Environment

**Q1. Which OCI region will the VM be provisioned in?**
Always Free Ampere A1 (ARM) capacity is genuinely constrained in some regions — this matters for whether provisioning succeeds on the first try. If you don't have a strong preference, pick whichever region you're already signed up under / closest to you.

[Answer]: Mumbai (ap-mumbai-1)

**Q2. OS image for the VM.**
A) Ubuntu 22.04 (ARM) — most k3s install guides and community troubleshooting assume Ubuntu
B) Oracle Linux 8 (ARM) — Oracle's own default recommendation, `firewalld`-based instead of `ufw`/`iptables` directly
C) Other (specify)

[Answer]: A

### Compute Infrastructure

**Q3. VM sizing within the Always Free Ampere A1 allocation (4 OCPU / 24GB RAM total, shareable across up to 4 VMs).**
A) One VM using the full allocation (4 OCPU / 24GB) — simplest, matches "single-node k3s cluster"
B) Split across multiple smaller VMs (not needed for a single-node k3s setup, but say so if you have another reason)

[Answer]: A

### Storage Infrastructure

**Q4. Boot volume and Postgres PVC sizing.**
Always Free includes up to 200GB total block storage. Proposed default: 50GB boot volume (OS + container images + k3s), ~20GB PVC for Postgres (generous for a demo's data volume) — well under the 200GB cap.
A) Use the proposed default (50GB boot / 20GB PVC)
B) Different sizing (specify)

[Answer]: A (use the proposed default: 50GB boot / 20GB PVC)

### Networking Infrastructure

Already fixed in NFR Design: Traefik ingress (bundled with k3s), security list open on 80/443/22 only, DuckDNS + reserved static IP. No further questions here — flagging for completeness per the category checklist.

### Monitoring Infrastructure

**Q5. Infra-level monitoring/logging scope for the VM/cluster itself** (separate from the app's own Unit 4 observability dashboard, which already covers application-level logs/metrics).
A) None — `kubectl logs` / `kubectl get pods` / SSH access is sufficient for a demo deployment
B) Add something lightweight (specify — e.g. `k9s` for terminal cluster browsing, basic `journalctl`/systemd status checks documented in the README)

[Answer]: A

### Shared Infrastructure

N/A — Unit 6 is the only unit needing infrastructure; there's no cross-unit infrastructure sharing to design.
