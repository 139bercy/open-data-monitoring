import React, { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import { SummaryStats } from "../components/analytics/SummaryStats";
import HeatmapContainer from "../containers/analytics/HeatmapContainer";
import { SidePanelContainer } from "../containers/analytics/SidePanelContainer";
import {
  DatasetDetailsModal,
  datasetDetailsModal,
} from "../components/DatasetDetailsModal";
import { getDatasetDetail, getPlatforms } from "../api/datasets";
import type { DatasetDetail, PlatformRef } from "../types/datasets";

export function Home(): JSX.Element {
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
      console.error("Error opening dataset details from Home:", error);
    }
  };

  return (
    <div
      className="fr-container fr-my-4w"
      style={{ position: "relative", overflowX: "hidden" }}
    >
      {/* Title & Stats */}
      <div className="fr-grid-row fr-grid-row--middle fr-mb-4w">
        <div className="fr-col">
          <h1 className="fr-h2 fr-mb-0">Tableau de Bord</h1>
        </div>
        <div className="fr-col-auto">
          <Link
            to="/datasets"
            className="fr-btn fr-btn--tertiary fr-btn--sm fr-icon-search-line fr-btn--icon-left"
          >
            Catalogue complet
          </Link>
        </div>
      </div>

      <SummaryStats />

      {/* Radar Section */}
      <section
        className="fr-mt-4w fr-p-2w"
        style={{
          backgroundColor: "var(--background-alt-grey)",
          border: "1px solid var(--border-default-grey)",
        }}
      >
        <HeatmapContainer onDirectionSelect={handleDirectionSelect} />
      </section>

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
    </div>
  );
}
