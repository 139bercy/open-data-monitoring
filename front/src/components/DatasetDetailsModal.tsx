import { useCallback, useEffect, useMemo, useState } from "react";
import { Accordion } from "@codegouvfr/react-dsfr/Accordion";
import { createModal } from "@codegouvfr/react-dsfr/Modal";
import { Button } from "@codegouvfr/react-dsfr/Button";
import { Alert } from "@codegouvfr/react-dsfr/Alert";
import { Tabs } from "@codegouvfr/react-dsfr/Tabs";
import { Badge } from "@codegouvfr/react-dsfr/Badge";
import type { DatasetDetail, SnapshotVersion } from "../types/datasets";
import {
  getDatasetVersions,
  evaluateDataset,
  getDatasetDetail,
} from "../api/datasets";
import {
  CompareSnapshotsModal,
  compareSnapshotsModal,
} from "./CompareSnapshotsModal";
import { calculateDownloadsPerDay } from "../utils/calculations";
import { computeDiff, DiffSummary } from "../utils/diff";

/**
 * Constants & Utils
 */
export const datasetDetailsModal = createModal({
  id: "dataset-details-modal",
  isOpenedByDefault: false,
});

export type DatasetDetailsModalProps = Readonly<{
  dataset?: DatasetDetail | null;
  platformName?: string | null;
  platformUrl?: string | null;
}>;

const copyToClipboard = async (text: string) => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.style.position = "absolute";
      textarea.style.left = "-999999px";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      textarea.remove();
    }
  } catch (err) {
    console.error("Erreur copie:", err);
  }
};

/**
 * Custom Hooks
 */
function useDatasetManager(initialDataset: DatasetDetail | null) {
  const [dataset, setDataset] = useState<DatasetDetail | null>(initialDataset);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setDataset(initialDataset);
  }, [initialDataset]);

  const refresh = useCallback(async () => {
    if (!dataset?.id) return;
    try {
      const updated = await getDatasetDetail(dataset.id, false);
      setDataset(updated);
    } catch (e) {
      console.error("Erreur refresh:", e);
    }
  }, [dataset?.id]);

  return { dataset, setDataset, loading, setLoading, refresh };
}

function useQualityAudit(datasetId?: string, onRefresh?: () => Promise<void>) {
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const evaluate = useCallback(async () => {
    if (!datasetId) return;
    setEvaluating(true);
    setError(null);
    try {
      await evaluateDataset(datasetId);
      if (onRefresh) await onRefresh();
    } catch (err: any) {
      setError(err.message ?? "L'audit a échoué");
    } finally {
      setEvaluating(false);
    }
  }, [datasetId, onRefresh]);

  return { evaluating, error, evaluate };
}

function useHistoryManager(datasetId?: string) {
  const [versions, setVersions] = useState<SnapshotVersion[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSnapshots, setSelectedSnapshots] = useState<Set<string>>(
    new Set()
  );

  const fetchVersions = useCallback(async () => {
    if (!datasetId) return;
    setVersions(null);
    setError(null);
    setLoading(true);
    try {
      const res = await getDatasetVersions(datasetId, {
        page: 1,
        pageSize: 90,
        includeData: true,
      });
      setVersions(res.items);
    } catch (e: any) {
      setError(e?.message ?? "Impossible de charger l'historique");
    } finally {
      setLoading(false);
    }
  }, [datasetId]);

  useEffect(() => {
    fetchVersions();
    setSelectedSnapshots(new Set());
  }, [datasetId, fetchVersions]);

  const toggleSelection = useCallback((id: string, checked: boolean) => {
    setSelectedSnapshots((prev) => {
      const next = new Set(prev);
      if (checked) {
        if (next.size >= 2) {
          const first = next.values().next().value;
          if (first !== undefined) next.delete(first);
        }
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  }, []);

  return {
    versions,
    loading,
    error,
    fetchVersions,
    selectedSnapshots,
    toggleSelection,
    setSelectedSnapshots,
  };
}

/**
 * Sub-components
 */
function SnapshotItem({
  snap,
  diff,
  selected = false,
  onSelect,
  displayCheckbox = false,
  isCurrent = false,
}: {
  snap: SnapshotVersion;
  diff?: DiffSummary;
  selected?: boolean;
  onSelect?: (id: string, checked: boolean) => void;
  displayCheckbox?: boolean;
  isCurrent?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const hasDiff =
    !!diff && diff.added.length + diff.removed.length + diff.changed.length > 0;

  return (
    <div
      className="fr-p-2w fr-mb-2w"
      onClick={() => setExpanded(!expanded)}
      style={{
        border: "1px solid var(--border-default-grey)",
        borderRadius: "4px",
        backgroundColor: selected
          ? "var(--background-alt-blue-france)"
          : "white",
        cursor: "pointer",
        position: "relative",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "1rem",
          flexWrap: "wrap",
        }}
      >
        {displayCheckbox && (
          <input
            type="checkbox"
            checked={selected}
            onClick={(e) => e.stopPropagation()}
            onChange={(e) => onSelect?.(snap.id, e.target.checked)}
            style={{ width: "1.2rem", height: "1.2rem", cursor: "pointer" }}
          />
        )}

        <div style={{ flex: 1 }}>
          <span className="fr-text--bold fr-mr-1w">
            {new Date(snap.timestamp).toLocaleDateString()}
          </span>
          <span
            className="fr-text--xs"
            style={{ color: "var(--text-mention-grey)" }}
          >
            {new Date(snap.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>

        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <Badge
            severity="info"
            noIcon
            small
          >
            {snap.apiCallsCount ?? "—"} API
          </Badge>
          <Badge
            severity="success"
            noIcon
            small
          >
            {snap.downloadsCount ?? "—"} DL
          </Badge>
          {isCurrent && (
            <Badge
              noIcon
              small
              style={{
                backgroundColor: "var(--background-flat-blue-france)",
                color: "white",
              }}
            >
              Actuel
            </Badge>
          )}
          {hasDiff && (
            <Badge
              severity="warning"
              small
            >
              Modifié
            </Badge>
          )}
          <span
            className={expanded ? "ri-arrow-up-s-line" : "ri-arrow-down-s-line"}
          />
        </div>
      </div>

      {expanded && (
        <div
          className="fr-mt-2w fr-p-2w"
          onClick={(e) => e.stopPropagation()}
          style={{
            backgroundColor: "var(--background-alt-grey)",
            borderRadius: "4px",
          }}
        >
          {hasDiff && (
            <div className="fr-mb-2w">
              <p className="fr-text--xs fr-text--bold fr-mb-1w">
                Différences :
              </p>
              <div style={{ display: "flex", gap: "1rem" }}>
                <span
                  className="fr-text--xs"
                  style={{ color: "var(--text-default-success)" }}
                >
                  +{diff!.added.length}
                </span>
                <span
                  className="fr-text--xs"
                  style={{ color: "var(--text-default-error)" }}
                >
                  -{diff!.removed.length}
                </span>
                <span
                  className="fr-text--xs"
                  style={{ color: "var(--text-default-info)" }}
                >
                  ~{diff!.changed.length}
                </span>
              </div>
            </div>
          )}
          <Button
            priority="tertiary"
            size="small"
            iconId="ri-file-copy-line"
            onClick={() =>
              copyToClipboard(JSON.stringify((snap as any).data, null, 2))
            }
            className="fr-mb-1w"
          >
            Copier JSON
          </Button>
          <pre
            className="fr-text--xs"
            style={{ maxHeight: "300px", overflow: "auto", margin: 0 }}
          >
            {JSON.stringify((snap as any).data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

function InfoTab({
  dataset,
  platformName,
  platformUrl,
  downloadsPerDay,
  versionsCount,
}: {
  dataset: DatasetDetail;
  platformName?: string | null;
  platformUrl?: string | null;
  downloadsPerDay: number | string | null;
  versionsCount: number;
}) {
  return (
    <div className="fr-py-4w">
      <div className="fr-mb-3w">
        <Badge
          severity={dataset.hasDescription ? "success" : "error"}
          noIcon
        >
          {dataset.hasDescription
            ? "Description renseignée"
            : "Description manquante"}
        </Badge>
      </div>
      <div className="fr-text--sm">
        <p>
          <strong>Plateforme:</strong>{" "}
          {platformUrl ? (
            <a
              href={platformUrl}
              target="_blank"
              rel="noreferrer"
            >
              {platformName}
            </a>
          ) : (
            platformName || dataset.platformId
          )}
        </p>
        <p>
          <strong>Producteur:</strong> {dataset.publisher ?? "—"}
        </p>
        <p>
          <strong>Créé le:</strong> {new Date(dataset.created).toLocaleString()}
        </p>
        <p>
          <strong>Modifié le:</strong>{" "}
          {new Date(dataset.modified).toLocaleString()}
        </p>
        <p>
          <strong>Téléchargements totaux :</strong>{" "}
          {dataset.currentSnapshot?.downloadsCount ?? "—"}
        </p>
        <p>
          <strong>Moyenne :</strong> {downloadsPerDay ?? "—"} DL/jour{" "}
          {versionsCount > 1 ? `(sur ${versionsCount} j)` : ""}
        </p>
      </div>
      <div className="fr-mt-4w">
        <Button
          iconId="ri-external-link-line"
          priority="secondary"
          onClick={() => window.open(dataset.page, "_blank")}
        >
          Voir sur la plateforme
        </Button>
      </div>
      {dataset.currentSnapshot && (
        <div className="fr-mt-6w">
          <h6 className="fr-h6">Snapshot courant</h6>
          <SnapshotItem
            snap={dataset.currentSnapshot}
            isCurrent
          />
        </div>
      )}
    </div>
  );
}

function QualityTab({
  dataset,
  evaluating,
  evalError,
  onEvaluate,
}: {
  dataset: DatasetDetail;
  evaluating: boolean;
  evalError: string | null;
  onEvaluate: () => void;
}) {
  const results = dataset.quality?.evaluation_results;
  const score = results?.overall_score ?? 0;

  return (
    <div className="fr-py-4w">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
        className="fr-mb-4w"
      >
        <h6 className="fr-h6 fr-mb-0">Audit Qualité (IA)</h6>
        <Button
          priority="secondary"
          size="small"
          iconId="ri-ai-generate"
          onClick={onEvaluate}
          disabled={evaluating || !!dataset.isDeleted}
        >
          {evaluating ? "Audit en cours..." : "Relancer l'audit"}
        </Button>
      </div>

      {evalError && (
        <Alert
          severity="error"
          title="Erreur"
          description={evalError}
          className="fr-mb-4w"
          small
        />
      )}

      {results ? (
        <>
          <Alert
            severity={
              score >= 70 ? "success" : score >= 50 ? "info" : "warning"
            }
            title={
              score >= 85
                ? "Excellente"
                : score >= 70
                  ? "Bonne"
                  : score >= 50
                    ? "Satisfaisante"
                    : "À améliorer"
            }
            description={
              score >= 70
                ? "Documentation de qualité."
                : "Améliorations suggérées."
            }
            className="fr-mb-4w"
          />
          <div
            className="fr-grid-row fr-grid-row--middle fr-p-3w fr-mb-4w"
            style={{
              backgroundColor: "var(--background-alt-blue-france)",
              borderRadius: "8px",
            }}
          >
            <div className="fr-col">
              <h5 className="fr-h5 fr-mb-1w">
                Score Global: {Math.round(score)}/100
              </h5>
              <p className="fr-text--xs fr-mb-0">
                Analysé le {new Date(results.evaluated_at).toLocaleString()}
              </p>
            </div>
          </div>
          <div className="fr-mb-6w">
            {["administrative", "descriptive", "geotemporal"].map((cat) => {
              const criteria = Object.entries(results.criteria_scores).filter(
                ([_, s]: any) => s.category === cat
              );
              return (
                criteria.length > 0 && (
                  <div
                    key={cat}
                    className="fr-mb-3w"
                  >
                    <p
                      className="fr-text--sm fr-text--bold"
                      style={{ textTransform: "uppercase" }}
                    >
                      {cat}
                    </p>
                    {criteria.map(([key, s]: any) => (
                      <Accordion
                        key={key}
                        label={`${s.criterion} — ${Math.round(s.score)}/100`}
                      >
                        <p className="fr-text--xs">
                          Poids: {(s.weight * 100).toFixed(0)}%
                        </p>
                        {s.issues.length > 0 ? (
                          <ul className="fr-text--xs">
                            {s.issues.map((i: string, idx: number) => (
                              <li key={idx}>{i}</li>
                            ))}
                          </ul>
                        ) : (
                          <p className="fr-text--xs fr-text--default-success">
                            Critère respecté
                          </p>
                        )}
                      </Accordion>
                    ))}
                  </div>
                )
              );
            })}
          </div>
          {results.suggestions?.length > 0 && (
            <div>
              <h6 className="fr-h6">Suggestions</h6>
              <div className="fr-grid-row fr-grid-row--gutters">
                {results.suggestions.map((s: any, i: number) => (
                  <div
                    key={i}
                    className="fr-col-12 fr-col-md-6"
                  >
                    <div
                      className="fr-card fr-p-2w"
                      style={{
                        borderLeft:
                          "4px solid var(--border-default-blue-france)",
                      }}
                    >
                      <p className="fr-badge fr-badge--sm fr-badge--info fr-mb-1w">
                        {s.field}
                      </p>
                      <p className="fr-text--sm">
                        <strong>Proposé:</strong> {s.suggested_value}
                      </p>
                      <p
                        className="fr-text--xs"
                        style={{ fontStyle: "italic" }}
                      >
                        {s.reason}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <p>Aucun audit disponible.</p>
      )}
    </div>
  );
}

function HistoryTab({
  versions,
  loading,
  error,
  refresh,
  selectedSnapshots,
  toggleSelection,
  onCompare,
  baseline,
}: {
  versions: SnapshotVersion[] | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
  selectedSnapshots: Set<string>;
  toggleSelection: (id: string, checked: boolean) => void;
  onCompare: () => void;
  baseline?: SnapshotVersion | null;
}) {
  return (
    <div className="fr-py-4w">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
        className="fr-mb-4w"
      >
        <h6 className="fr-h6 fr-mb-0">Historique ({versions?.length ?? 0})</h6>
        <Button
          iconId="ri-history-line"
          priority="tertiary"
          size="small"
          onClick={refresh}
        >
          {loading ? "..." : "Rafraîchir"}
        </Button>
      </div>

      {error && (
        <Alert
          severity="error"
          title="Erreur"
          description={error}
          className="fr-mb-4w"
        />
      )}

      {selectedSnapshots.size > 0 && (
        <Alert
          severity="info"
          title={
            selectedSnapshots.size === 2
              ? "Prêt à comparer"
              : "Sélectionnez une autre version"
          }
          description={
            selectedSnapshots.size === 2 ? (
              <Button
                size="small"
                onClick={onCompare}
                iconId="ri-arrow-left-right-line"
                className="fr-mt-2w"
              >
                Comparer
              </Button>
            ) : undefined
          }
          className="fr-mb-4w"
        />
      )}

      <div
        className="fr-pl-2w"
        style={{ borderLeft: "2px solid var(--border-default-grey)" }}
      >
        {versions?.map((s) => (
          <SnapshotItem
            key={s.id}
            snap={s}
            onSelect={toggleSelection}
            selected={selectedSnapshots.has(s.id)}
            displayCheckbox
            diff={baseline ? computeDiff(baseline.data, s.data) : undefined}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * Main Component
 */
export function DatasetDetailsModal({
  dataset: initialDataset,
  platformName,
  platformUrl,
}: DatasetDetailsModalProps): JSX.Element {
  const { dataset, refresh } = useDatasetManager(initialDataset || null);
  const {
    evaluating,
    error: evalError,
    evaluate,
  } = useQualityAudit(dataset?.id, refresh);
  const {
    versions,
    loading: loadingVersions,
    error: historyError,
    fetchVersions,
    selectedSnapshots,
    toggleSelection,
  } = useHistoryManager(dataset?.id);

  const downloadsPerDay = useMemo(
    () =>
      versions && versions.length >= 2
        ? calculateDownloadsPerDay(versions)
        : null,
    [versions]
  );

  const selectedSnapshotObjects = useMemo(() => {
    const ids = Array.from(selectedSnapshots);
    if (ids.length !== 2 || !versions) return null;
    const [snapA, snapB] = ids
      .map((id) => versions.find((v) => v.id === id))
      .filter(Boolean);
    return snapA && snapB ? { snapA, snapB } : null;
  }, [selectedSnapshots, versions]);

  if (!dataset)
    return (
      <datasetDetailsModal.Component title="Chargement...">
        <p>Patientez un instant...</p>
      </datasetDetailsModal.Component>
    );

  return (
    <>
      <datasetDetailsModal.Component
        title={undefined}
        size="large"
        style={{ minWidth: "85%" }}
      >
        <style>{`#dataset-details-modal .fr-modal__dialog { max-width: 85vw !important; }`}</style>

        <div
          className="fr-grid-row fr-grid-row--middle fr-mb-4w"
          style={{ marginTop: "-1rem" }}
        >
          <h1 className="fr-h3 fr-mb-0">{dataset.title ?? dataset.slug}</h1>
          <Badge
            noIcon
            small
            className="fr-ml-2w"
          >
            {dataset.slug}
          </Badge>
        </div>

        <Tabs
          tabs={[
            {
              label: "Informations",
              content: (
                <InfoTab
                  dataset={dataset}
                  platformName={platformName}
                  platformUrl={platformUrl}
                  downloadsPerDay={downloadsPerDay}
                  versionsCount={versions?.length ?? 0}
                />
              ),
            },
            {
              label: "Audit Qualité (IA)",
              content: (
                <QualityTab
                  dataset={dataset}
                  evaluating={evaluating}
                  evalError={evalError}
                  onEvaluate={evaluate}
                />
              ),
            },
            {
              label: "Historique",
              content: (
                <HistoryTab
                  versions={versions}
                  loading={loadingVersions}
                  error={historyError}
                  refresh={fetchVersions}
                  selectedSnapshots={selectedSnapshots}
                  toggleSelection={toggleSelection}
                  onCompare={compareSnapshotsModal.open}
                  baseline={dataset.currentSnapshot}
                />
              ),
            },
          ]}
        />
      </datasetDetailsModal.Component>

      {selectedSnapshotObjects && (
        <CompareSnapshotsModal
          snapshotA={selectedSnapshotObjects.snapA as SnapshotVersion}
          snapshotB={selectedSnapshotObjects.snapB as SnapshotVersion}
        />
      )}
    </>
  );
}
