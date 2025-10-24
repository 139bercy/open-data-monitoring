import { useCallback, useEffect, useMemo, useState } from "react";
import { Accordion } from "@codegouvfr/react-dsfr/Accordion";
import { createModal } from "@codegouvfr/react-dsfr/Modal";
import { Button } from "@codegouvfr/react-dsfr/Button";
import { Alert } from "@codegouvfr/react-dsfr/Alert";
import type { DatasetDetail, SnapshotVersion } from "../types/datasets";
import { getDatasetVersions } from "../api/datasets";
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
}): JSX.Element {
  const {
    snap,
    diff,
    selected = false,
    onSelect,
    displayCheckbox = false,
  } = props;
  const title = `${new Date(snap.timestamp).toLocaleString()} • API: ${snap.apiCallsCount ?? "—"} • DL: ${snap.downloadsCount ?? "—"}`;
  const hasDiff =
    !!diff && diff.added.length + diff.removed.length + diff.changed.length > 0;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        maxWidth: "80vh",
        overflow: "hidden",
      }}
    >
      {displayCheckbox && (
        <input
          id={`checkbox-${snap.id}`}
          type="checkbox"
          checked={selected}
          onChange={(e) => onSelect?.(snap.id, e.target.checked)}
          style={{ marginTop: "0.5rem", flexShrink: 0 }}
        />
      )}
      <div style={{ flex: 1, minWidth: 0, overflow: "hidden" }}>
        <Accordion label={title}>
          {hasDiff && (
            <div className="fr-mb-2w">
              <p className="fr-text--sm">
                <strong>Différences vs dernière version</strong>
              </p>
              <ul className="fr-pl-2w fr-text--sm">
                <li>Ajouts: {diff!.added.length}</li>
                <li>Suppressions: {diff!.removed.length}</li>
                <li>Modifications: {diff!.changed.length}</li>
              </ul>
            </div>
          )}

          {"data" in snap && (snap as any).data && (
            <div style={{ overflowX: "auto", maxWidth: "100%" }}>
              <pre
                className="fr-text--xs"
                aria-label="Snapshot JSON"
                style={{
                  whiteSpace: "pre-wrap",
                  wordWrap: "break-word",
                  margin: 0,
                  maxWidth: "100%",
                }}
              >
                {JSON.stringify((snap as any).data, null, 2)}
              </pre>
            </div>
          )}
        </Accordion>
      </div>
    </div>
  );
}

export function DatasetDetailsModal(
  props: DatasetDetailsModalProps
): JSX.Element {
  const { dataset, isOpen, onClose, platformName, platformUrl } = props;
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
      checked ? next.add(id) : next.delete(id);
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
        title={dataset?.slug ?? "Détails du dataset"}
        size="lg"
        isOpen={isOpen}
        onClose={onClose}
        style={{ minWidth: "85%" }}
      >
        {!dataset ? (
          <p className="fr-text">Chargement…</p>
        ) : (
          <>
            {error && (
              <Alert
                severity="error"
                title="Erreur"
                description={error}
                className="fr-mb-2w"
              />
            )}
            <div className="fr-mb-3w">
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
                Téléchargements totaux :{" "}
                {dataset.currentSnapshot?.downloadsCount}
              </p>
              <p className="fr-text--sm">
                Moyenne par jour{" "}
                {versions && versions.length >= 2
                  ? `(sur ${versions.length} j.)`
                  : ""}
                : {downloadsPerDay ?? "—"} téléchargements/jour
              </p>
              <a
                className="fr-link"
                href={dataset.page}
                target="_blank"
                rel="noreferrer"
              >
                Voir sur la plateforme
              </a>
            </div>

            {dataset.currentSnapshot && (
              <div className="fr-mb-2w">
                <h6 className="fr-h6">Snapshot courant</h6>
                <SnapshotItem snap={dataset.currentSnapshot} />
              </div>
            )}

            {Array.isArray(versions) &&
              versionsDatasetId === dataset.id &&
              versions.length > 0 && (
                <div className="fr-mt-4w">
                  <div className="fr-grid-row fr-grid-row--middle fr-grid-row--gutters fr-mb-2w">
                    <div className="fr-col">
                      <h6 className="fr-h6 fr-mb-0">
                        Historique des snapshots
                      </h6>
                    </div>
                    {selectedSnapshots.size === 2 && (
                      <div className="fr-col-auto">
                        <Button
                          onClick={handleCompareVersions}
                          priority="secondary"
                        >
                          Comparer les versions
                        </Button>
                      </div>
                    )}
                    <div className="fr-col-auto">
                      <Button
                        iconId="ri-history-line"
                        priority="secondary"
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
                              pageSize: 10,
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
                        {loadingVersions
                          ? "Chargement…"
                          : "Charger l'historique"}
                      </Button>
                    </div>
                  </div>

                  {versions.map((s) => (
                    <SnapshotItem
                      key={s.id}
                      snap={s}
                      diff={
                        baseline
                          ? computeDiff(baseline.data, s.data)
                          : undefined
                      }
                      selected={selectedSnapshots.has(s.id)}
                      onSelect={toggleSnapshotSelection}
                      displayCheckbox
                    />
                  ))}
                </div>
              )}
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
