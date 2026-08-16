import { apiJson } from "./client";
import type { MetricBucket } from "../types";

export function getMetrics(): Promise<MetricBucket[]> {
  // No client-side params in v1 - always requests the backend's own
  // defaults (last 1h, 60s buckets). See functional-design/frontend-components.md.
  return apiJson("/metrics");
}
