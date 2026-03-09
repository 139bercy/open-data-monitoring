import { useState, useEffect } from "react";
import api from "../api/api";

export interface HeatmapData {
  direction: string;
  score: number;
  crises: number;
  [key: string]: any;
}

export const useDirectionHealth = () => {
  const [data, setData] = useState<HeatmapData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await api.get<HeatmapData[]>(
          "/analytics/direction-health"
        );
        setData(result);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { data, loading, error };
};
