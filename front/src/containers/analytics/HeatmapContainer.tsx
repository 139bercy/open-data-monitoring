import React from "react";
import { useNavigate } from "react-router-dom";
import HeatmapPresenter from "../../components/analytics/HeatmapPresenter";
import { useDirectionHealth } from "../../hooks/useDirectionHealth";

const HeatmapContainer: React.FC = () => {
  const { data, loading, error } = useDirectionHealth();
  const navigate = useNavigate();

  if (loading)
    return <div className="fr-p-4w">Chargement du Radar de Santé...</div>;
  if (error)
    return <div className="fr-alert fr-alert--error fr-m-4w">{error}</div>;

  const handleClusterClick = (direction: string) => {
    navigate(`/datasets?publisher=${encodeURIComponent(direction)}`);
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
