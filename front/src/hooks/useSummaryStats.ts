import { useState, useEffect } from "react";
import api from "../api/api";

export interface SummaryStats {
  total_datasets: number;
  avg_health_score: number;
  total_publishers: number;
  crises_count: number;
  total_platforms: number;
}

export function useSummaryStats() {
  const [data, setData] = useState<SummaryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    api
      .get<SummaryStats>("/v1/analytics/summary")
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err);
        setLoading(false);
      });
  }, []);

  return { data, loading, error };
}
