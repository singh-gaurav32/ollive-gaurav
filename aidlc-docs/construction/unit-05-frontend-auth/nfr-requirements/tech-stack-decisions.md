# Tech Stack Decisions — Unit 5: Frontend Application + Auth/Isolation

## CORS over a dev proxy

A Vite proxy is simpler for local dev but solves nothing for production — Unit 6 would have to configure the same routing again in whatever reverse proxy fronts the deployed frontend. CORS, configured once via `ALLOWED_ORIGINS`, works identically in both environments; only the env var's value changes between them.

## Vite + React + TypeScript + Tailwind + TanStack Query

Confirmed from Functional Design Q2. New dependencies: `vite`, `react`, `react-dom`, `react-router-dom`, `@tanstack/react-query`, `tailwindcss` + `postcss`/`autoprefixer`, `typescript`.

## Vitest + React Testing Library

New dev dependencies: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom` (test environment). Vitest chosen over Jest since it shares Vite's config and transform pipeline directly — no separate babel/webpack setup to maintain alongside the app's own build.

## No password hashing library

Direct consequence of Functional Design Q1 (pick-a-user, no password) — `passlib`/`bcrypt` are not needed.
