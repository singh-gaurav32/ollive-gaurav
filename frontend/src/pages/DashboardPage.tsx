import { useMetrics } from "../hooks/useMetrics";
import { MetricsSummary } from "../components/MetricsSummary";

export function DashboardPage() {
  const { data: buckets, isLoading, error } = useMetrics();

  return (
    <div className="p-6">
      <h1 className="mb-4 text-lg font-semibold text-gray-900">Observability Dashboard</h1>
      {isLoading && <p className="text-sm text-gray-500">Loading metrics...</p>}
      {error && <p className="text-sm text-red-600">Failed to load metrics.</p>}
      {buckets && <MetricsSummary buckets={buckets} />}
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
                <td className="py-2">{new Date(b.bucket_start).toLocaleTimeString()}</td>
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
