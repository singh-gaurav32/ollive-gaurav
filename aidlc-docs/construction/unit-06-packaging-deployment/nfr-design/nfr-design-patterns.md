# NFR Design Patterns — Unit 6: Packaging & Deployment

## Networking / TLS

- **Ingress**: k3s's bundled **Traefik** ingress controller — no separate nginx-ingress install. One `Ingress` resource per public host route (frontend `/`, API under `/api`), or a single Ingress with path-based rules if the frontend proxies `/api` calls straight through to the `api` Service.
- **TLS**: **cert-manager** installed into the cluster, with a `ClusterIssuer` for Let's Encrypt using the **HTTP-01** challenge (works cleanly through Traefik with no extra DNS-API credentials, unlike DNS-01). The Ingress annotation `cert-manager.io/cluster-issuer` triggers automatic cert issuance/renewal.
- **Static IP + DNS**: reserve Oracle Cloud's free static public IP for the VM (see NFR Design plan's recommendation), point the DuckDNS `A` record at it once. No dynamic-DNS updater component needed in-cluster.

## Security

- **Secrets**: a single `Secret` manifest (`k8s/secrets.yaml`, git-ignored) holding `GEMINI_API_KEY` and Postgres credentials, referenced by the `api` and `postgres` Deployments via `envFrom`/`secretKeyRef`. No secrets manager, no sealed-secrets controller.
- **Firewall**: Oracle Cloud security list / VM firewall (`iptables` or `firewalld`, whichever the VM image uses) allowing only 80, 443, 22 inbound. No pattern needed beyond a static rule set applied once during VM setup.

## Storage

- **Postgres**: a `PersistentVolumeClaim` backed by k3s's default `local-path` storage class (local VM disk). No StatefulSet needed — a single-replica `Deployment` + PVC is sufficient at this scale (k3s's default storage class doesn't support multi-node ReadWriteMany anyway, which is fine for a single-node cluster).

## Resilience / Scalability / Performance

N/A — explicitly out of scope per `nfr-requirements.md` (single-node demo deployment, no HA/autoscaling/backup requirements).
