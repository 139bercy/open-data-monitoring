import React from "react";
import HeatmapContainer from "../containers/analytics/HeatmapContainer";

export const RadarHealthPage: React.FC = () => {
  return (
    <main className="fr-container fr-pb-8w">
      <div className="fr-grid-row">
        <div className="fr-col-12">
          <HeatmapContainer />
        </div>
      </div>
    </main>
  );
};
