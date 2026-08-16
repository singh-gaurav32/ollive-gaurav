# Functional Design Plan — Unit 5: Frontend Application + Auth/Isolation

## Execution Checklist

- [x] Confirm demo login mechanism (see Question 1) — A
- [x] Confirm frontend page/route structure (see Question 2) — A
- [x] Confirm cancel-during-streaming interaction (see Question 3) — A
- [x] Generate `business-logic-model.md`
- [x] Generate `business-rules.md`
- [x] Generate `domain-entities.md`
- [x] Generate `frontend-components.md`

## Technical note, decided directly (not a question)

The chat streaming endpoint (`POST /conversations/{id}/messages`) takes a JSON body, so the browser's native `EventSource` (GET-only) can't be used to consume it. The frontend will use `fetch()` with a `ReadableStream` reader instead, parsing the `event: token` / `data: ...` framing manually. This isn't a new choice — it's a direct consequence of the endpoint shape Unit 2 already fixed — but worth stating since it shapes how the chat view is built.

---

## Question 1: Demo login mechanism
Requirements Analysis fixed "session-based auth with a few seeded demo users" but not the login flow itself.

A) **Pick-a-user, no password** — the login screen lists the seeded demo usernames; clicking one calls a login endpoint that creates a session for that user. Fastest to build and demo, appropriate for a take-home where Security Baseline was explicitly declined.

B) **Username + password**, a handful of seeded credential pairs — closer to a real login flow, requires password hashing (`passlib`/`bcrypt`) as a new dependency for a feature whose only consumers are the seeded demo accounts.

C) Other (please describe after [Answer]: tag below)

[Answer]: A — pick-a-user, no password.

## Question 2: Frontend page/route structure
A) **Four routes**: `/login`, `/chat` (list + active conversation), `/chat/:conversationId` (resume a specific one), `/dashboard`. Standard React Router setup, `Vite + React + TypeScript` as the toolchain, Tailwind for styling, TanStack Query for server-state (conversations, messages, metrics) fetching/caching.

B) Same routes, but without a dedicated data-fetching library — plain `useState`/`useEffect` and manual `fetch` calls. Fewer dependencies, more boilerplate, no caching/refetch-on-focus behavior for the dashboard.

C) Other (please describe after [Answer]: tag below)

[Answer]: A — Vite + React + TypeScript + Tailwind + TanStack Query.

## Question 3: Cancel-during-streaming interaction
The cancel button fires `POST /conversations/{id}/cancel` while the chat view's `fetch()` stream-read is still in progress.

A) Cancel button calls the cancel endpoint; the frontend also aborts its own `fetch()` read via `AbortController` as soon as it's sent, so the UI stops rendering new tokens immediately rather than waiting for the backend's cancellation to propagate back through the (now-closing) stream

B) Cancel button only calls the cancel endpoint; the frontend keeps reading the stream until the backend closes it naturally (whatever partial content was in flight before cancellation still renders, then stops) — simpler, marginally slower perceived responsiveness

C) Other (please describe after [Answer]: tag below)

[Answer]: A — abort the frontend's own stream read via AbortController immediately, in addition to calling the cancel endpoint.
