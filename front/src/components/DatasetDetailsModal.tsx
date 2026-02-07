import { useCallback, useEffect, useMemo, useState } from "react";
import { Accordion } from "@codegouvfr/react-dsfr/Accordion";
import { createModal } from "@codegouvfr/react-dsfr/Modal";
import { Button } from "@codegouvfr/react-dsfr/Button";
import { Alert } from "@codegouvfr/react-dsfr/Alert";
import { Tabs } from "@codegouvfr/react-dsfr/Tabs";
import { Badge } from "@codegouvfr/react-dsfr/Badge";
import type { DatasetDetail, SnapshotVersion } from "../types/datasets";
import { getDatasetVersions, evaluateDataset, getDatasetDetail } from "../api/datasets";
import {
  CompareSnapshotsModal,
  compareSnapshotsModal,
} from "./CompareSnapshotsModal";
import { calculateDownloadsPerDay } from "../utils/calculations";
import { computeDiff, DiffSummary } from "../utils/diff";

export const datasetDetailsModal = createModal({
  id: "dataset-details-modal",
  isOpenedByDefault: false,
});

export type DatasetDetailsModalProps = Readonly<{
  dataset?: DatasetDetail | null;
  platformName?: string | null;
  platformUrl?: string | null;
}>;

function SnapshotItem(props: {
  snap: SnapshotVersion;
  diff?: DiffSummary;
  selected?: boolean;
  onSelect?: (id: string, checked: boolean) => void;
  displayCheckbox?: boolean;
  isCurrent?: boolean;
}): JSX.Element {
  const {
    snap,
    diff,
    selected = false,
    onSelect,
    displayCheckbox = false,
    isCurrent = false,
  } = props;
  
  const [expanded, setExpanded] = useState(false);

  const hasDiff =
    !!diff && diff.added.length + diff.removed.length + diff.changed.length > 0;

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

  return (
    <div
      className="fr-p-2w fr-mb-2w"
      onClick={() => setExpanded(!expanded)}
      style={{
        border: "1px solid var(--border-default-grey)",
        borderRadius: "4px",
        backgroundColor: selected ? "var(--background-alt-blue-france)" : "white",
        transition: "all 0.2s",
        cursor: "pointer",
        position: "relative"
      }}
      onMouseOver={(e) => {
        if (!selected) e.currentTarget.style.backgroundColor = "var(--background-alt-grey)";
      }}
      onMouseOut={(e) => {
        if (!selected) e.currentTarget.style.backgroundColor = "white";
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
        {displayCheckbox && (
          <input
            id={`checkbox-${snap.id}`}
            type="checkbox"
            checked={selected}
            onClick={(e) => e.stopPropagation()} // Prevent card toggle when clicking checkbox
            onChange={(e) => onSelect?.(snap.id, e.target.checked)}
            style={{ width: "1.2rem", height: "1.2rem", margin: 0, cursor: "pointer" }}
          />
        )}
        
        <div style={{ flex: 1, minWidth: "150px" }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem" }}>
            <span className="fr-text--bold fr-mb-0">
              {new Date(snap.timestamp).toLocaleDateString()}
            </span>
            <span className="fr-text--xs" style={{ color: "var(--text-mention-grey)" }}>
              {new Date(snap.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </div>

        {expanded && "data" in snap && (snap as any).data && (
          <div style={{ flex: "1 0 auto", textAlign: "center" }}>
            <Button
              priority="tertiary"
              size="small"
              iconId="ri-file-copy-line"
              onClick={(e) => {
                e.stopPropagation();
                copyToClipboard(JSON.stringify((snap as any).data, null, 2));
              }}
            >
              Copier le JSON
            </Button>
          </div>
        )}

        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center", marginLeft: "auto" }}>
          <Badge severity="info" noIcon small>
            {snap.apiCallsCount ?? "—"} API
          </Badge>
          <Badge severity="success" noIcon small>
            {snap.downloadsCount ?? "—"} DL
          </Badge>
          {isCurrent && (
            <Badge noIcon small style={{ backgroundColor: "var(--background-flat-blue-france)", color: "white" }}>
              Actuel
            </Badge>
          )}
          {hasDiff && (
            <Badge severity="warning" small>
              Modifié
            </Badge>
          )}
          <span 
            className={expanded ? "ri-arrow-up-s-line" : "ri-arrow-down-s-line"} 
            style={{ marginLeft: "0.5rem", color: "var(--text-mention-grey)" }}
          />
        </div>
      </div>

      {expanded && (
        <div 
          className="fr-mt-2w fr-p-2w" 
          onClick={(e) => e.stopPropagation()} // Prevent closing when interacting with content
          style={{ 
            backgroundColor: "var(--background-alt-grey)", 
            borderRadius: "4px",
            borderLeft: "4px solid var(--border-default-blue-france)",
            cursor: "default"
          }}
        >
          {hasDiff && (
            <div className="fr-mb-2w fr-p-2w fr-background-alt--grey" style={{ borderRadius: "4px" }}>
              <p className="fr-text--xs fr-text--bold fr-mb-1w">Différences détectées :</p>
              <div style={{ display: "flex", gap: "1rem" }}>
                <span className="fr-text--xs" style={{ color: "var(--text-default-success)" }}>+{diff!.added.length}</span>
                <span className="fr-text--xs" style={{ color: "var(--text-default-error)" }}>-{diff!.removed.length}</span>
                <span className="fr-text--xs" style={{ color: "var(--text-default-info)" }}>~{diff!.changed.length}</span>
              </div>
            </div>
          )}

          {"data" in snap && (snap as any).data && (
            <pre
              className="fr-text--xs fr-p-2w"
              style={{
                backgroundColor: "var(--background-alt-grey)",
                borderRadius: "4px",
                maxHeight: "300px",
                overflow: "auto",
                whiteSpace: "pre-wrap",
                wordWrap: "break-word",
                margin: 0
              }}
            >
              {JSON.stringify((snap as any).data, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

export function DatasetDetailsModal(
  props: DatasetDetailsModalProps
): JSX.Element {
  const { dataset: initialDataset, platformName, platformUrl } = props;
  const [dataset, setDataset] = useState<DatasetDetail | null>(initialDataset || null);
  const [evaluating, setEvaluating] = useState(false);
  const [evalError, setEvalError] = useState<string | null>(null);
  
  useEffect(() => {
    setDataset(initialDataset || null);
  }, [initialDataset]);

  const refreshDataset = async () => {
    if (!dataset?.id) return;
    try {
      const updated = await getDatasetDetail(dataset.id, false);
      setDataset(updated);
    } catch (e) {
      console.error("Erreur refresh:", e);
    }
  };

  const handleEvaluate = async () => {
    if (!dataset?.id) return;
    setEvaluating(true);
    setEvalError(null);
    try {
      await evaluateDataset(dataset.id);
      await refreshDataset();
    } catch (err: any) {
      setEvalError(err.message ?? "L'audit a échoué");
    } finally {
      setEvaluating(false);
    }
  };

  const [loadingVersions, setLoadingVersions] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [versions, setVersions] = useState<SnapshotVersion[] | null>(null);
  const [versionsDatasetId, setVersionsDatasetId] = useState<string | null>(
    null
  );
  const [selectedSnapshots, setSelectedSnapshots] = useState<Set<string>>(
    new Set()
  );
  const [renderKey, setRenderKey] = useState(0);

  useEffect(() => {
    setRenderKey((r) => r + 1);
  }, [dataset?.id]);

  useEffect(() => {
    setSelectedSnapshots(new Set());
  }, [dataset?.id]);

  const toggleSnapshotSelection = (id: string, checked: boolean) => {
    setSelectedSnapshots((prev) => {
      const next = new Set(prev);
      if (checked) {
        if (next.size >= 2) {
          // Keep only the most recent selection if already 2
          const first = next.values().next().value;
          if (first !== undefined) next.delete(first);
        }
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  };

  useEffect(() => {
    let active = true;
    if (!dataset?.id) return;
    setVersions(null);
    setVersionsDatasetId(dataset.id);
    setError(null);
    setLoadingVersions(true);
    (async () => {
      try {
        const res = await getDatasetVersions(dataset.id, {
          page: 1,
          pageSize: 90,
          includeData: true,
        });
        if (active) setVersions(res.items);
      } catch (e: any) {
        if (active)
          setError(e?.message ?? "Impossible de charger l'historique");
      } finally {
        if (active) setLoadingVersions(false);
      }
    })();

    return () => {
      active = false;
    };
  }, [dataset?.id]);

  const downloadsPerDay = useMemo(() => {
    return versions && versions.length >= 2
      ? calculateDownloadsPerDay(versions)
      : null;
  }, [versions]);

  const baseline = useMemo<SnapshotVersion | null>(() => {
    if (dataset?.currentSnapshot) return dataset.currentSnapshot;
    if (versionsDatasetId === dataset?.id && versions && versions.length > 0)
      return versions[0];
    return null;
  }, [dataset?.currentSnapshot, dataset?.id, versions, versionsDatasetId]);

  const selectedSnapshotObjects = useMemo(() => {
    const ids = Array.from(selectedSnapshots);
    if (ids.length !== 2 || !versions) return null;

    const snapA = versions.find((v) => v.id === ids[0]);
    const snapB = versions.find((v) => v.id === ids[1]);

    return snapA && snapB ? { snapA, snapB } : null;
  }, [selectedSnapshots, versions]);

  const handleCompareVersions = useCallback(() => {
    if (selectedSnapshotObjects?.snapA && selectedSnapshotObjects?.snapB) {
      compareSnapshotsModal.open();
    }
  }, [selectedSnapshotObjects]);

  return (
    <>
      <datasetDetailsModal.Component
        title={undefined}
        size="large"
        style={{ minWidth: "85%" }}
      >
        <style>{`
          #dataset-details-modal .fr-modal__dialog {
            max-width: 85vw !important;
          }
          #dataset-details-modal .fr-container {
            max-width: 85% !important;
            width: 85% !important;
          }
        `}</style>
        {!dataset ? (
          <p className="fr-text">Chargement…</p>
        ) : (
          <>
            <div className="fr-grid-row fr-grid-row--middle fr-mb-4w" style={{ marginTop: "-1rem" }}>
              <div className="fr-col">
                <div style={{ display: "flex", alignItems: "baseline", gap: "1rem", flexWrap: "wrap" }}>
                  <h1 className="fr-h3 fr-mb-0">{dataset.title ?? dataset.slug}</h1>
                  <Badge noIcon small style={{ textTransform: "none", backgroundColor: "var(--background-alt-grey)", color: "var(--text-mention-grey)" }}>
                    {dataset.slug}
                  </Badge>
                </div>
              </div>
            </div>

            {error && (
              <Alert
                severity="error"
                title="Erreur"
                description={error}
                className="fr-mb-2w"
              />
            )}

            <Tabs
              tabs={[
                {
                  label: "Informations",
                  content: (
                    <div className="fr-py-4w">
                      <div className="fr-mb-3w">
                        <span
                          className={`fr-badge ${
                            dataset.hasDescription
                              ? "fr-badge--success"
                              : "fr-badge--error"
                          }`}
                        >
                          {dataset.hasDescription ? "Description renseignée" : "Description manquante"}
                        </span>
                      </div>
                      <p className="fr-text--sm">
                        <strong>Plateforme:</strong>{" "}
                        {platformName ? (
                          platformUrl ? (
                            <a
                              className="fr-link fr-text--sm"
                              href={platformUrl}
                              target="_blank"
                              rel="noreferrer"
                            >
                              {platformName}
                            </a>
                          ) : (
                            platformName
                          )
                        ) : (
                          dataset.platformId
                        )}
                      </p>
                      <p className="fr-text--sm">
                        <strong>Producteur:</strong> {dataset.publisher ?? "—"}
                      </p>
                      <p className="fr-text--sm">
                        <strong>Créé le:</strong>{" "}
                        {new Date(dataset.created).toLocaleString()}
                      </p>
                      <p className="fr-text--sm">
                        <strong>Modifié le:</strong>{" "}
                        {new Date(dataset.modified).toLocaleString()}
                      </p>
                      <p className="fr-text--sm">
                        <strong>Téléchargements totaux :</strong>{" "}
                        {dataset.currentSnapshot?.downloadsCount ?? "—"}
                      </p>
                      <p className="fr-text--sm">
                        <strong>Moyenne par jour :</strong> {downloadsPerDay ?? "—"} téléchargements/jour
                        {versions && versions.length >= 2 ? ` (sur ${versions.length} jours)` : ""}
                      </p>
                      <div className="fr-mt-4w">
                        <a
                          className="fr-btn fr-btn--secondary fr-btn--icon-left ri-external-link-line"
                          href={dataset.page}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Voir sur la plateforme source
                        </a>
                      </div>

                      {dataset.currentSnapshot && (
                        <div className="fr-mt-6w">
                          <h6 className="fr-h6">Snapshot courant</h6>
                          <SnapshotItem snap={dataset.currentSnapshot} isCurrent />
                        </div>
                      )}
                    </div>
                  )
                },
                {
                  label: "Audit Qualité (IA)",
                  content: (
                    <div className="fr-py-4w">
                      <div className="fr-grid-row fr-grid-row--middle fr-mb-4w">
                        <div className="fr-col">
                          <h6 className="fr-h6 fr-mb-0">Analyse de la qualité des métadonnées</h6>
                        </div>
                        <div className="fr-col-auto">
                          <Button
                            priority="secondary"
                            size="small"
                            iconId={evaluating ? undefined : "ri-ai-generate"}
                            onClick={handleEvaluate}
                            disabled={evaluating || dataset.isDeleted === true}
                          >
                            {evaluating ? "Audit en cours..." : "Relancer l'audit"}
                          </Button>
                        </div>
                      </div>

                      {evalError && (
                        <Alert
                          severity="error"
                          title="Erreur lors de l'audit"
                          description={evalError}
                          className="fr-mb-4w"
                          small
                        />
                      )}

                      {!dataset.isDeleted && dataset.quality?.evaluation_results ? (
                        <>
                          <Alert
                            severity={
                              dataset.quality.evaluation_results.overall_score >= 70 ? "success" : 
                              dataset.quality.evaluation_results.overall_score >= 50 ? "info" : 
                              "warning"
                            }
                            title={
                              dataset.quality.evaluation_results.overall_score >= 85 ? "Qualité Excellente" :
                              dataset.quality.evaluation_results.overall_score >= 70 ? "Bonne Qualité" :
                              dataset.quality.evaluation_results.overall_score >= 50 ? "Qualité Satisfaisante" :
                              "Qualité à améliorer"
                            }
                            description={
                              dataset.quality.evaluation_results.overall_score >= 70 
                                ? "Ce jeu de données respecte la majorité des bonnes pratiques de documentation."
                                : "Des améliorations significatives sont possibles pour faciliter la réutilisation."
                            }
                            className="fr-mb-4w"
                          />

                          <div className="fr-p-3w fr-mb-4w" style={{ backgroundColor: "var(--background-alt-blue-france)", borderRadius: "8px" }}>
                            <div className="fr-grid-row fr-grid-row--middle">
                              <div className="fr-col">
                                <h5 className="fr-h5 fr-mb-1w">Score Global</h5>
                                <p className="fr-text--xs fr-mb-0" style={{ color: "var(--text-mention-grey)" }}>
                                  Dernière analyse le {new Date(dataset.quality.evaluation_results.evaluated_at).toLocaleString()}
                                </p>
                              </div>
                              <div className="fr-col-auto">
                                <div className="fr-p-2w" style={{ 
                                  borderRadius: "50%", 
                                  width: "100px", 
                                  height: "100px", 
                                  display: "flex", 
                                  flexDirection: "column",
                                  alignItems: "center", 
                                  justifyContent: "center",
                                  border: "6px solid",
                                  borderColor: dataset.quality.evaluation_results.overall_score >= 70 ? "var(--text-default-success)" : 
                                               dataset.quality.evaluation_results.overall_score >= 50 ? "var(--text-default-warning)" : 
                                               "var(--text-default-error)",
                                  backgroundColor: "white",
                                  boxShadow: "var(--shadow-raised-grey)"
                                }}>
                                  <span className="fr-h2 fr-mb-0" style={{ fontWeight: "bold", lineHeight: 1 }}>
                                    {Math.round(dataset.quality.evaluation_results.overall_score)}
                                  </span>
                                  <span className="fr-text--xs" style={{ fontWeight: "bold", color: "var(--text-mention-grey)" }}>/100</span>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="fr-mb-6w">
                            <h6 className="fr-h6 fr-mb-3w">Détail par catégories</h6>
                            {/* Grouping by category */}
                            {["administrative", "descriptive", "geotemporal"].map(category => {
                              const criteria = Object.entries(dataset.quality!.evaluation_results!.criteria_scores)
                                .filter(([_, s]: [string, any]) => s.category === category);
                              
                              if (criteria.length === 0) return null;

                              const catLabel = category === "administrative" ? "Administratif" :
                                             category === "descriptive" ? "Descriptif" : "Géo-temporel";
                              const catIcon = category === "administrative" ? "ri-file-list-3-line" :
                                            category === "descriptive" ? "ri-text-spacing" : "ri-map-pin-time-line";

                              return (
                                <div key={category} className="fr-mb-3w">
                                  <div className="fr-flex fr-mb-1w" style={{ alignItems: "center", gap: "0.5rem" }}>
                                    <span className={catIcon} aria-hidden="true" style={{ color: "var(--text-title-blue-france)" }}></span>
                                    <span className="fr-text--sm fr-text--bold fr-mb-0" style={{ textTransform: "uppercase", letterSpacing: "1px", color: "var(--text-title-blue-france)" }}>
                                      {catLabel}
                                    </span>
                                  </div>
                                  {criteria.map(([key, score]: [string, any]) => (
                                    <Accordion key={key} label={`${score.criterion} — ${Math.round(score.score)}/100`}>
                                      <div className="fr-text--sm">
                                        <p className="fr-mb-2w" style={{ fontStyle: "italic", color: "var(--text-mention-grey)" }}>
                                          Poids dans le score : {(score.weight * 100).toFixed(0)}%
                                        </p>
                                        {score.issues.length > 0 ? (
                                          <div className="fr-background-contrast--info fr-p-2w" style={{ borderRadius: "4px" }}>
                                            <p className="fr-text--xs fr-text--bold fr-mb-1w">Points d'attention :</p>
                                            <ul className="fr-text--xs fr-mb-0">
                                              {score.issues.map((issue: string, idx: number) => (
                                                <li key={idx} className="fr-mb-1v">{issue}</li>
                                              ))}
                                            </ul>
                                          </div>
                                        ) : (
                                          <p className="fr-mb-0 fr-text--default-success fr-mt-2w fr-text--bold">
                                            <span className="ri-checkbox-circle-line fr-mr-1v" aria-hidden="true"></span>
                                            Critère respecté
                                          </p>
                                        )}
                                      </div>
                                    </Accordion>
                                  ))}
                                </div>
                              );
                            })}
                          </div>

                          {dataset.quality.evaluation_results.suggestions && dataset.quality.evaluation_results.suggestions.length > 0 && (
                            <div>
                              <h6 className="fr-h6 fr-mb-3w">Suggestions d'amélioration</h6>
                              <div className="fr-grid-row fr-grid-row--gutters">
                                {dataset.quality.evaluation_results.suggestions.map((s: any, idx: number) => {
                                  let icon = "ri-lightbulb-line";
                                  if (s.field.toLowerCase().includes('titre')) icon = "ri-text-line";
                                  if (s.field.toLowerCase().includes('desc')) icon = "ri-article-line";
                                  if (s.field.toLowerCase().includes('mots')) icon = "ri-price-tag-3-line";
                                  if (s.field.toLowerCase().includes('date')) icon = "ri-calendar-line";
                                  if (s.field.toLowerCase().includes('producteur')) icon = "ri-community-line";

                                  return (
                                    <div key={idx} className="fr-col-12 fr-col-md-6 fr-mb-2w">
                                      <div className="fr-card fr-card--sm fr-p-3w" style={{ height: "100%", borderLeft: "4px solid var(--border-default-blue-france)", boxShadow: "var(--shadow-raised-grey)" }}>
                                        <div className="fr-card__body">
                                          <div className="fr-flex fr-mb-1w" style={{ alignItems: "center", gap: "0.5rem" }}>
                                            <span className={icon} style={{ color: "var(--text-default-info)" }}></span>
                                            <span className="fr-badge fr-badge--sm fr-badge--info">
                                              {s.field}
                                            </span>
                                          </div>
                                          <p className="fr-text--sm fr-mb-2w"><strong>Proposition :</strong> {Array.isArray(s.suggested_value) ? s.suggested_value.join(', ') : s.suggested_value}</p>
                                          <p className="fr-text--xs fr-mb-0" style={{ fontStyle: "italic", color: "var(--text-mention-grey)" }}>{s.reason}</p>
                                        </div>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          )}
                        </>
                      ) : (
                        <div className="fr-py-12w fr-grid-row fr-grid-row--center">
                          <div className="fr-col-12 fr-col-md-8" style={{ textAlign: "center" }}>
                            <p className="fr-text--lg fr-mb-4w">Aucun audit n'a encore été réalisé pour ce jeu de données.</p>
                            <Button
                              priority="primary"
                              iconId="ri-ai-generate"
                              onClick={handleEvaluate}
                              disabled={evaluating || dataset.isDeleted === true}
                            >
                              Lancer l'audit maintenant
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  )
                },
                {
                  label: "Historique",
                  content: (
                    <div className="fr-py-4w">
                      <div className="fr-mb-4w">
                        <div className="fr-grid-row fr-grid-row--middle fr-mb-2w">
                          <div className="fr-col">
                            <h6 className="fr-h6 fr-mb-0">
                              Parcours temporel des snapshots
                            </h6>
                            <p className="fr-text--xs fr-mb-0" style={{ color: "var(--text-mention-grey)" }}>
                              {versions?.length ?? 0} versions enregistrées
                            </p>
                          </div>
                          <div className="fr-col-auto">
                            <Button
                              iconId="ri-history-line"
                              priority="tertiary"
                              size="small"
                              disabled={loadingVersions}
                              onClick={async () => {
                                if (!dataset) return;
                                setVersions(null);
                                setVersionsDatasetId(dataset.id);
                                try {
                                  setError(null);
                                  setLoadingVersions(true);
                                  const res = await getDatasetVersions(dataset.id, {
                                    page: 1,
                                    pageSize: 90,
                                    includeData: true,
                                  });
                                  setVersions(res.items);
                                } catch (e: any) {
                                  setError(
                                    e?.message ?? "Impossible de charger l'historique"
                                  );
                                } finally {
                                  setLoadingVersions(false);
                                }
                              }}
                            >
                              {loadingVersions ? "Chargement…" : "Rafraîchir"}
                            </Button>
                          </div>
                        </div>

                        {selectedSnapshots.size > 0 && (
                          <div className="fr-p-2w fr-mb-4w" style={{ backgroundColor: "var(--background-alt-blue-france)", border: "1px solid var(--border-default-blue-france)", borderRadius: "4px" }}>
                            <div className="fr-grid-row fr-grid-row--middle">
                              <div className="fr-col">
                                <p className="fr-text--sm fr-text--bold fr-mb-0">
                                  {selectedSnapshots.size === 1 
                                    ? "Sélectionnez une deuxième version pour comparer"
                                    : "2 versions sélectionnées"}
                                </p>
                              </div>
                              {selectedSnapshots.size === 2 && (
                                <div className="fr-col-auto">
                                  <Button
                                    onClick={handleCompareVersions}
                                    priority="primary"
                                    size="small"
                                    iconId="ri-arrow-left-right-line"
                                  >
                                    Lancer la comparaison
                                  </Button>
                                </div>
                              )}
                              <div className="fr-col-auto fr-ml-2w">
                                <Button
                                  priority="tertiary"
                                  size="small"
                                  onClick={() => setSelectedSnapshots(new Set())}
                                >
                                  Annuler
                                </Button>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="fr-pl-2w" style={{ borderLeft: "2px solid var(--border-default-grey)", marginLeft: "0.5rem" }}>
                        {Array.isArray(versions) && versions.length > 0 ? (
                          versions.map((s) => (
                            <SnapshotItem
                              key={s.id}
                              snap={s}
                              isCurrent={s.id === dataset.currentSnapshot?.id}
                              diff={
                                baseline
                                  ? computeDiff(baseline.data, s.data)
                                  : undefined
                              }
                              selected={selectedSnapshots.has(s.id)}
                              onSelect={toggleSnapshotSelection}
                              displayCheckbox
                            />
                          ))
                        ) : (
                          <div className="fr-py-6w" style={{ textAlign: "center" }}>
                            <p className="fr-text--sm fr-text--mention-grey">Aucun historique disponible ou en attente de chargement.</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                }
              ]}
            />
          </>
        )}
      </datasetDetailsModal.Component>
      {selectedSnapshotObjects && (
        <CompareSnapshotsModal
          snapshotA={selectedSnapshotObjects.snapA}
          snapshotB={selectedSnapshotObjects.snapB}
        />
      )}
    </>
  );
}
