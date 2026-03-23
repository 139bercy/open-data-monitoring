import React, { useState } from "react";
import { Link } from "react-router-dom";
import HeatmapPresenter from "../../components/analytics/HeatmapPresenter";
import { useDirectionHealth } from "../../hooks/useDirectionHealth";

interface HeatmapContainerProps {
  onDirectionSelect?: (direction: string) => void;
}

const HeatmapContainer: React.FC<HeatmapContainerProps> = ({
  onDirectionSelect,
}) => {
  const { data, loading, error } = useDirectionHealth();
  const [selectedDirection, setSelectedDirection] = useState<string | null>(
    null
  );

  if (loading)
    return <div className="fr-p-4w">Chargement du Radar de Santé...</div>;
  if (error)
    return <div className="fr-alert fr-alert--error fr-m-4w">{error}</div>;

  const handleClusterClick = (direction: string) => {
    setSelectedDirection(direction);
    if (onDirectionSelect) {
      onDirectionSelect(direction);
    }
  };

  const datasetsUrl = selectedDirection
    ? `/datasets?publisher=${encodeURIComponent(selectedDirection)}`
    : "/datasets";

  return (
    <div className="fr-container">
      <h2
        className="fr-h4 fr-mt-4w"
        style={{ display: "flex", alignItems: "center", gap: "8px" }}
      >
        Radar de Santé des jeux de données par Direction
        {selectedDirection && (
          <Link
            to={datasetsUrl}
            className="fr-link fr-text--sm"
            style={{ fontWeight: "normal", fontSize: "0.85rem" }}
            title={`Voir les datasets de : ${selectedDirection}`}
          >
            → {selectedDirection}
          </Link>
        )}
      </h2>
      <HeatmapPresenter
        data={data}
        onClusterClick={handleClusterClick}
      />
    </div>
  );
};

export default HeatmapContainer;
