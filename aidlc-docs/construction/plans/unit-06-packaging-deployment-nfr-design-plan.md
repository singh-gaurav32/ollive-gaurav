# Unit 6 — Packaging & Deployment — NFR Design Plan

## Steps
- [x] Analyze NFR requirements for design implications
- [x] Assess whether a user question round is needed
- [x] Generate `nfr-design-patterns.md` and `logical-components.md`

## Assessment: no question round needed

All NFR Requirements decisions (nginx frontend, build-on-VM, DuckDNS, k8s Secrets, PVC, manual deploys) are mechanical to realize — they translate directly into standard k8s objects with no open design fork, **except one**, which is resolved below by recommendation rather than a question since it has no real tradeoff:

**Static IP vs. dynamic DNS updater.** DuckDNS was chosen so the hostname survives an IP change — but Oracle Cloud's Always Free tier includes a free **reserved (static) public IP**. Reserving it once and pointing the DuckDNS `A` record at it means the hostname never needs to change and no DuckDNS-updater cronjob is required in the cluster. This strictly dominates a dynamic-updater approach (simpler, no extra moving part, still free) — recommendation adopted, not asked as a question.

Resilience/Scalability/Performance patterns: N/A per nfr-requirements.md (single-node demo, explicitly out of scope).
