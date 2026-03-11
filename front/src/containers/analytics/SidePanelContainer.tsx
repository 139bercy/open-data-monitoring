import React, { useEffect, useState } from "react";
import { SidePanelPresenter } from "../../components/analytics/SidePanelPresenter";
import { getDatasets } from "../../api/datasets";
import type { DatasetSummary } from "../../types/datasets";

export interface SidePanelContainerProps {
  isOpen: boolean;
  direction: string | null;
  onClose: () => void;
  onDatasetClick: (id: string) => void;
}

export const SidePanelContainer: React.FC<SidePanelContainerProps> = ({
  isOpen,
  direction,
  onClose,
  onDatasetClick,
}) => {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && direction) {
      const fetchDatasets = async () => {
        setLoading(true);
        try {
          const result = await getDatasets({
            publisher: direction,
            pageSize: 100, // Load enough for a quick view
          });
          setDatasets(result.items);
        } catch (error) {
          console.error("Error fetching datasets for side panel:", error);
          setDatasets([]);
        } finally {
          setLoading(false);
        }
      };
      fetchDatasets();
    } else {
      setDatasets([]);
    }
  }, [isOpen, direction]);

  return (
    <SidePanelPresenter
      isOpen={isOpen}
      direction={direction || ""}
      datasets={datasets}
      loading={loading}
      onClose={onClose}
      onDatasetClick={onDatasetClick}
    />
  );
};
