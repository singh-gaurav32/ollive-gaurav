import { useQuery } from "@tanstack/react-query";
import { getMetrics, type MetricsQuery } from "../api/metrics";

export function useMetrics(query: MetricsQuery = {}) {
  return useQuery({
    queryKey: ["metrics", query.bucketSizeSeconds, query.windowHours],
    queryFn: () => getMetrics(query),
    refetchInterval: 30_000, // poll-based dashboard (Requirements Analysis Q10)
  });
}
