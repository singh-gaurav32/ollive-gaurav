import { apiJson } from "./client";
import type { MetricBucket } from "../types";

export interface MetricsQuery {
  bucketSizeSeconds?: number;
  windowHours?: number;
}

export function getMetrics(query: MetricsQuery = {}): Promise<MetricBucket[]> {
  const params = new URLSearchParams();
  if (query.bucketSizeSeconds) {
    params.set("bucket_size_seconds", String(query.bucketSizeSeconds));
  }
  if (query.windowHours) {
    const end = new Date();
    const start = new Date(end.getTime() - query.windowHours * 60 * 60 * 1000);
    params.set("start", start.toISOString());
    params.set("end", end.toISOString());
  }
  const qs = params.toString();
  return apiJson(`/metrics${qs ? `?${qs}` : ""}`);
}
