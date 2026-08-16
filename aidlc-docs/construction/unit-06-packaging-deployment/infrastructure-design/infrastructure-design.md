# Infrastructure Design — Unit 6: Packaging & Deployment

## Compute

- **VM**: single Oracle Cloud Ampere A1 (ARM) instance, **`ap-mumbai-1`** region, using the full Always Free allocation — 4 OCPU / 24GB RAM.
- **OS**: Ubuntu 22.04 (ARM/aarch64) — chosen for k3s install/community-doc alignment (most k3s troubleshooting assumes Ubuntu's `ufw`/`systemd` conventions).
- **Known risk**: Ampere A1 free-tier capacity in `ap-mumbai-1` (and other regions) is known to fluctuate — "Out of host capacity" errors on provisioning are a common, documented Oracle Free Tier experience, not specific to this project. If provisioning fails repeatedly, the fallback recorded from earlier planning applies: a Hetzner (~€4/mo) or DigitalOcean (~$4-6/mo) VPS running the identical k3s setup — the `k8s/` manifests are host-agnostic, so no design work is lost.

## Kubernetes

- **k3s**, single-node (server, no separate agents) — installed via Rancher's standard install script (`curl -sfL https://get.k3s.io | sh -`), which brings Traefik and `local-path-provisioner` by default (matches NFR Design's chosen ingress and storage class — no extra install for either).
- **cert-manager**: installed separately (Helm or the official static manifest) as one-time cluster setup, not part of the app's own `k8s/` manifests — it's cluster infrastructure, not app deployment.

## Storage

- **Boot volume**: 50GB (OS, container images built directly on the VM, k3s runtime).
- **Postgres PVC**: 20GB, via k3s's default `local-path` storage class (backed by the VM's boot/block volume).
- Total: 70GB against Oracle's Always Free 200GB block-storage cap — comfortable headroom for image layers accumulating over time.

## Networking

- **Public IP**: Oracle Cloud reserved (static) public IP, attached to the VM — free tier includes one.
- **DNS**: DuckDNS subdomain, `A` record pointed at the reserved IP once (no updater needed since the IP doesn't change).
- **Security list / VM firewall**: inbound 80 (HTTP), 443 (HTTPS), 22 (SSH) only; all other inbound denied. No egress restrictions (needed for `docker build`/`apt`/Let's Encrypt validation/Gemini API calls).
- **TLS termination**: at Traefik, via cert-manager's Let's Encrypt HTTP-01-issued certificate.

## Monitoring / Operations

- No additional infra-level monitoring stack. Operational visibility is `kubectl get pods` / `kubectl logs` / SSH + `journalctl` for the k3s systemd service — sufficient for a single-node demo deployment, consistent with the "no CI/CD, manual deploys" maintainability decision from NFR Requirements.
- Application-level observability is already covered by Unit 4's dashboard — this unit doesn't duplicate that.

## Shared Infrastructure

N/A — Unit 6 is the sole unit with infrastructure needs; nothing is shared across units.
