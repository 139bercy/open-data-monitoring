import React from "react";
import { useSummaryStats } from "../../hooks/useSummaryStats";

export const SummaryStats: React.FC = () => {
  const { data, loading, error } = useSummaryStats();

  if (loading)
    return <div className="fr-p-2w">Chargement des statistiques...</div>;
  if (error || !data) return null;

  const stats = [
    {
      label: "Jeux de données",
      value: data.total_datasets,
      color: "var(--text-label-blue-france)",
    },
    {
      label: "Santé Globale",
      value: `${Math.round(data.avg_health_score)}%`,
      color:
        data.avg_health_score > 80
          ? "#18753c"
          : data.avg_health_score > 50
            ? "#b34000"
            : "#e1000f",
    },
    {
      label: "Directions",
      value: data.total_publishers,
      color: "var(--text-label-purple-glycine)",
    },
    {
      label: "Alertes",
      value: data.crises_count,
      color: data.crises_count > 0 ? "#e1000f" : "#18753c",
    },
  ];

  return (
    <div className="fr-grid-row fr-grid-row--gutters fr-mb-4w">
      {stats.map((stat, i) => (
        <div
          key={i}
          className="fr-col-6 fr-col-md-3"
        >
          <div
            className="fr-p-2w"
            style={{
              backgroundColor: "var(--background-alt-grey)",
              borderBottom: `2px solid ${stat.color}`,
              textAlign: "center",
            }}
          >
            <p
              className="fr-text--xs fr-mb-1v"
              style={{ opacity: 0.6, textTransform: "uppercase" }}
            >
              {stat.label}
            </p>
            <p
              className="fr-h4 fr-mb-0"
              style={{ color: stat.color, fontWeight: "bold" }}
            >
              {stat.value}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};
