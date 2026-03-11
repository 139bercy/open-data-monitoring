import React from "react";
import HeatmapPresenter from "../../components/analytics/HeatmapPresenter";
import { useDirectionHealth } from "../../hooks/useDirectionHealth";

interface HeatmapContainerProps {
  onDirectionSelect?: (direction: string) => void;
}

const HeatmapContainer: React.FC<HeatmapContainerProps> = ({
  onDirectionSelect,
}) => {
  const { data, loading, error } = useDirectionHealth();

  if (loading)
    return <div className="fr-p-4w">Chargement du Radar de Santé...</div>;
  if (error)
    return <div className="fr-alert fr-alert--error fr-m-4w">{error}</div>;

  const handleClusterClick = (direction: string) => {
    if (onDirectionSelect) {
      onDirectionSelect(direction);
    }
  };

  return (
    <div className="fr-container">
      <h2 className="fr-h4 fr-mt-4w">Radar de Santé par Direction</h2>
      <HeatmapPresenter
        data={data}
        onClusterClick={handleClusterClick}
      />
    </div>
  );
};

export default HeatmapContainer;
