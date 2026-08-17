import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="border-t border-gray-200 py-8 first:border-t-0 first:pt-0">
      <h2 className="mb-3 text-lg font-semibold text-gray-900">{title}</h2>
      <div className="space-y-3 text-sm leading-relaxed text-gray-700">{children}</div>
    </section>
  );
}

function Term({ term, children }: { term: string; children: React.ReactNode }) {
  return (
    <div>
      <span className="font-medium text-gray-900">{term}</span>
      <span className="text-gray-700"> — {children}</span>
    </div>
  );
}

export function AboutPage() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3">
        <span className="font-semibold text-gray-900">Ollive</span>
        <Link
          to={user ? "/chat" : "/login"}
          className="rounded bg-gray-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-700"
        >
          {user ? "Open the app" : "Try it — log in"}
        </Link>
      </div>

      <div className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="text-2xl font-semibold text-gray-900">Ollive</h1>
        <p className="mt-2 text-base text-gray-600">
          A chatbot with an auto-instrumented logging layer: every LLM call is captured, validated,
          PII-redacted, and persisted through an event-driven ingestion pipeline, with an observability
          dashboard built on top.
        </p>

        <Section title="What it does">
          <ul className="list-disc space-y-2 pl-5">
            <li>Chat with an LLM (Gemini by default, OpenAI via an env var swap) with streaming responses and mid-stream cancel.</li>
            <li>
              Every call is automatically logged — latency, time-to-first-token, input/output tokens,
              status, a redacted preview of the content — without a single manual logging call anywhere
              in the chat code.
            </li>
            <li>Logged content is PII-redacted (email, phone, SSN, credit-card patterns) before it's ever written to durable storage.</li>
            <li>An observability dashboard shows request volume, error rate, and p50/p95 latency over a configurable time window and bucket size.</li>
            <li>Per-user data isolation is real, not cosmetic — a second user sees zero of another user's conversations, enforced at the query layer, not hidden in the UI.</li>
          </ul>
        </Section>

        <Section title="High-Level Design">
          <p>System-level view: major subsystems, external dependencies, and how data flows between them.</p>
          <img
            src="/diagrams/hld.svg"
            alt="High-level architecture: browser talks to the FastAPI backend's auth, chat, and dashboard modules over a session cookie; chat calls the provider module, which calls the external LLM API and also auto-publishes a LogEvent to the events queue without blocking; the ingestion module consumes that queue and persists to Postgres; chat and dashboard read/write Postgres directly."
            className="w-full rounded-md border border-gray-200 bg-white p-2"
          />
          <p>
            The ingestion worker runs as a background task <em>inside</em> the same API process, not a
            separate service — one fewer moving part for a demo-scale deployment, at the cost of the API
            and ingestion sharing fate if the worker crashes (which is caught and logged loudly, not
            silently). The frontend is a Vite/React SPA; deployment packages Postgres, the API, and the
            frontend as three containers, the same shape locally (<code>docker-compose.yml</code>) and on
            the live k3s deployment (<code>k8s/</code>).
          </p>
        </Section>

        <Section title="Low-Level Design">
          <p>
            Two components carry the interesting design decisions in this system; the rest is a
            predictable, repetitive pattern (interface + one implementation) that's more useful to browse
            in the actual directory tree below than to diagram class-by-class.
          </p>

          <h3 className="pt-2 text-sm font-semibold text-gray-900">LLM provider — Strategy + Decorator</h3>
          <img
            src="/diagrams/lld-provider.svg"
            alt="LLMProvider is an interface implemented by GeminiProvider and OpenAIProvider (Strategy), and also by InstrumentedProvider, which wraps another LLMProvider and adds transparent logging (Decorator) by publishing a LogEvent to the EventQueue interface without blocking the call."
            className="w-full rounded-md border border-gray-200 bg-white p-2"
          />

          <h3 className="pt-4 text-sm font-semibold text-gray-900">Ingestion pipeline</h3>
          <img
            src="/diagrams/lld-ingestion.svg"
            alt="IngestionWorker consumes LogEvents from the EventQueue and runs each one through four stages in order: PayloadValidator, MetadataExtractor, PIIRedactor, then LogPersister, which maps to LogRepository. A failure at any stage is dead-lettered to FailedLogEventRepository, with no preview text ever included, and the loop continues to the next event."
            className="w-full rounded-md border border-gray-200 bg-white p-2"
          />

          <h3 className="pt-4 text-sm font-semibold text-gray-900">Everything else, by directory</h3>
          <pre className="overflow-x-auto rounded-md bg-gray-900 p-4 text-xs leading-relaxed text-gray-100">
{`backend/src/
  auth/        session-based auth, seeded demo users
  chat/        ChatService - conversation lifecycle, streaming + cancel
  provider/    LLMProvider, GeminiProvider/OpenAIProvider, InstrumentedProvider (see above)
  events/      EventQueue interface + InProcessEventQueue
  ingestion/   IngestionWorker + pipeline stages (see above)
  api/         routers (auth, chat, dashboard) + deps.py, the composition root
  db/          repository interfaces + SQLAlchemy implementations + Alembic migrations
  analytics/   thin AnalyticsService delegating to LogRepository

frontend/src/
  api/         fetch wrappers, one file per backend router
  hooks/       React Query hooks + useChatStream (hand-parsed SSE client)
  components/  presentational components
  pages/       route-level composition
  context/     AuthContext`}
          </pre>
        </Section>

        <Section title="Design decisions">
          <p>Three deliberate GoF patterns, each named directly in the code's own docstrings rather than left implicit:</p>
          <div className="space-y-2">
            <Term term="Strategy">
              <code>LLMProvider</code> is an interface with interchangeable implementations
              (<code>GeminiProvider</code>, <code>OpenAIProvider</code>), selected at runtime by a small
              factory reading the <code>LLM_PROVIDER</code> env var. Swapping providers requires zero
              changes to chat logic, ingestion, the dashboard, or the frontend.
            </Term>
            <Term term="Decorator">
              <code>InstrumentedProvider</code> wraps any <code>LLMProvider</code> to add transparent
              auto-logging. It's the single interception point for observability — nothing about
              capturing metadata lives in the chat service or the API routers.
            </Term>
            <Term term="Repository">
              Every persistence dependency (<code>ConversationRepository</code>,
              <code> LogRepository</code>, etc.) is an abstract interface with a SQLAlchemy
              implementation, keeping the ORM entirely invisible outside <code>db/</code> — business
              logic reads and writes plain domain models, never ORM rows.
            </Term>
          </div>
          <p className="pt-2">A few tradeoffs made deliberately, not by default:</p>
          <ul className="list-disc space-y-2 pl-5">
            <li>
              <strong>In-process event queue, not a real broker</strong> (Redis/Kafka/SQS) — zero extra
              infrastructure at this scale, at the cost of events being lost on a process crash. The
              <code> EventQueue</code> interface boundary already exists to swap this later without
              touching the ingestion worker or the instrumentation layer.
            </li>
            <li>
              <strong>Window-based context truncation</strong> (last 10 turns, hard cutoff) instead of
              summarization — simple, predictable token cost, at the cost of the model losing older
              context outright rather than gracefully.
            </li>
            <li>
              <strong>Session-based demo auth, no passwords</strong> — enough to demonstrate real
              per-user data isolation without building credential management that adds no value to what's
              being evaluated here.
            </li>
            <li>
              <strong>Hand-mirrored TypeScript types</strong>, not generated from the backend's schema —
              no extra build tooling, at the cost of manual upkeep if a backend field changes.
            </li>
          </ul>
        </Section>

        <Section title="Failure handling">
          <ul className="list-disc space-y-2 pl-5">
            <li>Provider call failures are always surfaced to the user, never swallowed into a silent empty response.</li>
            <li>Instrumentation failures (a full log queue, a dropped event) are always swallowed — observability failing must never take down the chat feature it's observing.</li>
            <li>Ingestion pipeline failures are dead-lettered with the failing stage recorded, never dropped silently and never crash the worker loop.</li>
            <li>A worker crash is logged loudly and immediately, not left to asyncio's default (silent until garbage collection).</li>
            <li>Cancelling a conversation mid-stream is a first-class, distinctly logged status — not treated as an error.</li>
          </ul>
        </Section>

        <Section title="What I'd improve with more time">
          <ul className="list-disc space-y-2 pl-5">
            <li>The OpenAI provider is unit-tested against a mock only, not verified against the real API (no chargeable key was available).</li>
            <li>No rate limiting on LLM calls beyond a response-length cap.</li>
            <li>No visible error toast on a failed chat send — the app recovers correctly but silently.</li>
            <li>No automated Postgres backup for the live deployment.</li>
            <li>No drill-down from the dashboard into individual failing requests, only aggregate counts.</li>
          </ul>
        </Section>
      </div>
    </div>
  );
}
