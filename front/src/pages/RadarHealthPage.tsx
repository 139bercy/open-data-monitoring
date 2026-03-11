import React, { useState, useEffect, useMemo } from "react";
import HeatmapContainer from "../containers/analytics/HeatmapContainer";
import { SidePanelContainer } from "../containers/analytics/SidePanelContainer";
import {
  DatasetDetailsModal,
  datasetDetailsModal,
} from "../components/DatasetDetailsModal";
import { getDatasetDetail, getPlatforms } from "../api/datasets";
import type { DatasetDetail, PlatformRef } from "../types/datasets";

export const RadarHealthPage: React.FC = () => {
  const [selectedDirection, setSelectedDirection] = useState<string | null>(
    null
  );
  const [isSidePanelOpen, setIsSidePanelOpen] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<DatasetDetail | null>(
    null
  );
  const [platforms, setPlatforms] = useState<PlatformRef[]>([]);

  // load ref data once (platforms)
  useEffect(() => {
    getPlatforms()
      .then(setPlatforms)
      .catch(() => undefined);
  }, []);

  // Resolve platform_id -> platform info for display
  const platformInfoById = useMemo(() => {
    const map = new Map<string, PlatformRef>();
    platforms.forEach((p) => map.set(p.id, p));
    return map;
  }, [platforms]);

  const handleDirectionSelect = (direction: string) => {
    setSelectedDirection(direction);
    setIsSidePanelOpen(true);
  };

  const handleDatasetClick = async (id: string) => {
    try {
      const detail = await getDatasetDetail(id, false);
      setSelectedDataset(detail);
      datasetDetailsModal.open();
    } catch (error) {
      console.error("Error opening dataset details from side panel:", error);
    }
  };

  return (
    <main
      className="fr-container fr-pb-8w"
      style={{ position: "relative", overflowX: "hidden" }}
    >
      <div className="fr-grid-row">
        <div className="fr-col-12">
          <HeatmapContainer onDirectionSelect={handleDirectionSelect} />
        </div>
      </div>

      <SidePanelContainer
        isOpen={isSidePanelOpen}
        direction={selectedDirection}
        onClose={() => setIsSidePanelOpen(false)}
        onDatasetClick={handleDatasetClick}
      />

      <DatasetDetailsModal
        dataset={selectedDataset}
        platformName={
          selectedDataset
            ? (platformInfoById.get(selectedDataset.platformId)?.name ?? null)
            : null
        }
        platformUrl={(() => {
          if (!selectedDataset?.page) return null;
          try {
            return new URL(selectedDataset.page).origin;
          } catch {
            return null;
          }
        })()}
        onClose={() => setSelectedDataset(null)}
      />
    </main>
  );
};
