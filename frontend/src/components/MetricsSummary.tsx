import type { MetricBucket } from "../types";

function totalRequests(buckets: MetricBucket[]): number {
  return buckets.reduce((sum, b) => sum + b.request_count, 0);
}

function totalErrors(buckets: MetricBucket[]): number {
  return buckets.reduce((sum, b) => sum + b.error_count, 0);
}

function latestP95(buckets: MetricBucket[]): number | null {
  const withLatency = [...buckets].reverse().find((b) => b.p95_latency_ms !== null);
  return withLatency?.p95_latency_ms ?? null;
}

export function MetricsSummary({ buckets }: { buckets: MetricBucket[] }) {
  const requests = totalRequests(buckets);
  const errors = totalErrors(buckets);
  const errorRate = requests > 0 ? ((errors / requests) * 100).toFixed(1) : "0.0";
  const p95 = latestP95(buckets);

  return (
    <div className="grid grid-cols-3 gap-4">
      <StatTile label="Requests (last 1h)" value={requests.toString()} />
      <StatTile label="Error rate" value={`${errorRate}%`} />
      <StatTile label="p95 latency" value={p95 !== null ? `${p95.toFixed(0)}ms` : "—"} />
    </div>
  );
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-gray-900">{value}</div>
    </div>
  );
}
