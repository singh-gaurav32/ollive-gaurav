import { useState } from "react";
import { useMetrics } from "../hooks/useMetrics";
import { MetricsSummary } from "../components/MetricsSummary";

const BUCKET_SIZE_OPTIONS = [
  { label: "30s", value: 30 },
  { label: "1m", value: 60 },
  { label: "5m", value: 300 },
  { label: "15m", value: 900 },
  { label: "1h", value: 3600 },
];

const WINDOW_OPTIONS = [
  { label: "Last 1h", value: 1 },
  { label: "Last 6h", value: 6 },
  { label: "Last 24h", value: 24 },
];

export function DashboardPage() {
  const [bucketSizeSeconds, setBucketSizeSeconds] = useState(60);
  const [windowHours, setWindowHours] = useState(1);
  const { data: buckets, isLoading, error } = useMetrics({ bucketSizeSeconds, windowHours });
  const windowLabel = WINDOW_OPTIONS.find((o) => o.value === windowHours)?.label.toLowerCase() ?? "last 1h";

  return (
    <div className="p-6">
      <h1 className="mb-4 text-lg font-semibold text-gray-900">Observability Dashboard</h1>
      <div className="mb-4 flex gap-4 text-sm">
        <label className="flex items-center gap-2">
          Bucket size
          <select
            data-testid="dashboard-bucket-size-select"
            value={bucketSizeSeconds}
            onChange={(e) => setBucketSizeSeconds(Number(e.target.value))}
            className="rounded border border-gray-300 px-2 py-1"
          >
            {BUCKET_SIZE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2">
          Range
          <select
            data-testid="dashboard-window-select"
            value={windowHours}
            onChange={(e) => setWindowHours(Number(e.target.value))}
            className="rounded border border-gray-300 px-2 py-1"
          >
            {WINDOW_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      {isLoading && <p className="text-sm text-gray-500">Loading metrics...</p>}
      {error && <p className="text-sm text-red-600">Failed to load metrics.</p>}
      {buckets && <MetricsSummary buckets={buckets} windowLabel={windowLabel} />}
      {buckets && buckets.length > 0 && (
        <table className="mt-6 w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-gray-500">
              <th className="py-2">Bucket</th>
              <th className="py-2">Requests</th>
              <th className="py-2">Errors</th>
              <th className="py-2">p50</th>
              <th className="py-2">p95</th>
            </tr>
          </thead>
          <tbody>
            {buckets.map((b) => (
              <tr key={b.bucket_start} className="border-b border-gray-100">
                <td className="py-2">
                  {new Date(b.bucket_start).toLocaleTimeString()}–{new Date(b.bucket_end).toLocaleTimeString()}
                </td>
                <td className="py-2">{b.request_count}</td>
                <td className="py-2">{b.error_count}</td>
                <td className="py-2">{b.p50_latency_ms?.toFixed(0) ?? "—"}ms</td>
                <td className="py-2">{b.p95_latency_ms?.toFixed(0) ?? "—"}ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
