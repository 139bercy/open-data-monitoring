import React from "react";
import { Button } from "@codegouvfr/react-dsfr/Button";
import { Badge } from "@codegouvfr/react-dsfr/Badge";
import type { DatasetSummary } from "../../types/datasets";

export interface SidePanelPresenterProps {
  isOpen: boolean;
  direction: string;
  datasets: DatasetSummary[];
  loading?: boolean;
  onClose: () => void;
  onDatasetClick: (id: string) => void;
}

export const SidePanelPresenter: React.FC<SidePanelPresenterProps> = ({
  isOpen,
  direction,
  datasets,
  loading,
  onClose,
  onDatasetClick,
}) => {
  if (!isOpen) return null;

  return (
    <div
      className="fr-drawer"
      style={{
        position: "fixed",
        top: 0,
        right: 0,
        bottom: 0,
        width: "400px",
        backgroundColor: "var(--background-default-grey)",
        zIndex: 1500,
        boxShadow: "-2px 0 10px rgba(0,0,0,0.1)",
        display: "flex",
        flexDirection: "column",
        transition: "transform 0.3s ease-in-out",
        transform: isOpen ? "translateX(0)" : "translateX(100%)",
      }}
    >
      <div
        className="fr-drawer__header fr-p-2w"
        style={{
          borderBottom: "1px solid var(--border-default-grey)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h2 className="fr-h4 fr-mb-0">{direction}</h2>
        <Button
          priority="tertiary no outline"
          iconId="fr-icon-close-line"
          onClick={onClose}
          title="Fermer"
          aria-label="Fermer"
        />
      </div>

      <div
        className="fr-drawer__body fr-p-2w"
        style={{ flex: 1, overflowY: "auto" }}
      >
        {loading ? (
          <div className="fr-skeleton">Chargement des données...</div>
        ) : datasets.length === 0 ? (
          <p className="fr-text--sm">
            Aucun jeu de données trouvé pour cette direction.
          </p>
        ) : (
          <ul className="fr-raw-list">
            {datasets.map((ds) => (
              <li
                key={ds.id}
                className="fr-p-2w fr-mb-1w"
                style={{
                  border: "1px solid var(--border-default-grey)",
                  borderRadius: "4px",
                  cursor: "pointer",
                  transition: "background-color 0.2s",
                }}
                onClick={() => onDatasetClick(ds.id)}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.backgroundColor =
                    "var(--background-alt-grey)")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.backgroundColor = "transparent")
                }
              >
                <div className="fr-text--bold fr-mb-1v">{ds.title}</div>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span
                    className="fr-text--xs"
                    style={{ color: "var(--text-mention-grey)" }}
                  >
                    {ds.publisher}
                  </span>
                  {ds.healthScore !== undefined && (
                    <Badge
                      severity={
                        ds.healthScore >= 85
                          ? "success"
                          : ds.healthScore >= 70
                            ? "info"
                            : ds.healthScore >= 50
                              ? "warning"
                              : "error"
                      }
                      noIcon
                      small
                    >
                      {Math.round(ds.healthScore)}%
                    </Badge>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
