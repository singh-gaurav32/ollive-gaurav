# Personas

## Persona 1: Chat User

**Role**: End user of the chatbot application.

**Goals**:
- Have natural multi-turn conversations and get fast, streaming answers.
- Manage their own conversation history — list, resume, and cancel conversations.
- Trust that their conversations are private and not visible to other users.

**Characteristics**: Not technical. Expects standard chat-app UX (comparable to ChatGPT/Claude's web app). Impatient with latency — expects visible progress, not a silent wait. May want to stop a response mid-generation if it's clearly off-track.

**Pain points if unmet**: Waiting for a full response with no feedback; losing context after resuming a conversation; seeing another user's data (an isolation failure that would erode trust immediately).

## Persona 2: Operator/Analyst

**Role**: The person operating and maintaining the deployed system. In this solo-build context, this is the same person as the builder, wearing an operations/reliability hat rather than a product hat — the persona exists to separate "things done to make the chatbot usable" from "things done to make the system observable, safe, and extensible."

**Goals**:
- Understand system health at a glance via the dashboard (latency, throughput, errors) rather than reading raw logs.
- Trust that PII is not leaking into logs or the database.
- Extend the system (add a provider, swap the event broker) without deep rework.
- Bring the system up locally with one command, and deploy it to a live environment reliably.

**Characteristics**: Technical. Cares about correctness under concurrency, extensibility, and compliance. Consumes aggregated metrics, not individual users' conversation content.

**Pain points if unmet**: Blind to production issues with no dashboard; compliance risk from raw PII in storage; forced rewrites to add a provider or change infrastructure; fragile or manual deployment process.

## Notes

- These two personas are intentionally the only ones in scope, per the confirmed story plan — no separate "admin" or "billing" persona exists yet.
- The Operator/Analyst persona also carries the technical/architectural stories (redaction, non-blocking logging, provider extensibility) per the confirmed plan's decision to include operator/technical stories rather than leaving them as prose-only NFRs.
