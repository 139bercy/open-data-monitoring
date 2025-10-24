import {useEffect, useMemo, useState} from "react";
import {Accordion} from "@codegouvfr/react-dsfr/Accordion";
import {createModal} from "@codegouvfr/react-dsfr/Modal";
import {Button} from "@codegouvfr/react-dsfr/Button";
import {Alert} from "@codegouvfr/react-dsfr/Alert";
import type {DatasetDetail, SnapshotVersion} from "../types/datasets";
import {getDatasetVersions} from "../api/datasets";
import {compareSnapshotsModal, CompareSnapshotsModal} from "./CompareSnapshotsModal";


export const datasetDetailsModal = createModal({
    id: "dataset-details-modal",
    isOpenedByDefault: false,
});

export type DatasetDetailsModalProps = Readonly<{
    dataset?: DatasetDetail | null;
    platformName?: string | null;
    platformUrl?: string | null;
}>;

type DiffSummary = {
    added: string[];
    removed: string[];
    changed: string[];
};

function flattenObject(value: unknown, prefix = ""): Record<string, unknown> {
    if (value === null || typeof value !== "object") {
        return { [prefix || "value"]: value };
    }
    const out: Record<string, unknown> = {};
    const obj = value as Record<string, unknown>;
    for (const key of Object.keys(obj)) {
        const next = prefix ? `${prefix}.${key}` : key;
        const v = obj[key];
        if (v !== null && typeof v === "object" && !Array.isArray(v)) {
            Object.assign(out, flattenObject(v, next));
        } else {
            out[next] = v;
        }
    }
    return out;
}

function computeDiff(base: unknown, other: unknown): DiffSummary {
    const a = flattenObject(base ?? {});
    const b = flattenObject(other ?? {});
    const added: string[] = [];
    const removed: string[] = [];
    const changed: string[] = [];
    const aKeys = new Set(Object.keys(a));
    const bKeys = new Set(Object.keys(b));
    for (const k of bKeys) {
        if (!aKeys.has(k)) {
            added.push(k);
        } else {
            const av = JSON.stringify(a[k]);
            const bv = JSON.stringify(b[k]);
            if (av !== bv) changed.push(k);
        }
    }
    for (const k of aKeys) {
        if (!bKeys.has(k)) removed.push(k);
    }
    return { added, removed, changed };
}

function SnapshotItem(props: {
    snap: SnapshotVersion;
    diff?: DiffSummary;
    selected?: boolean;
    onSelect?: (id: string, checked: boolean) => void;
    displayCheckbox?: boolean;
}): JSX.Element {
    const { snap, diff, selected = false, onSelect, displayCheckbox = false } = props;  // destructuré avec valeur par défaut
    const title = `${new Date(snap.timestamp).toLocaleString()} • API: ${snap.apiCallsCount ?? "—"} • DL: ${snap.downloadsCount ?? "—"}`;
    const hasDiff = !!diff && (diff.added.length + diff.removed.length + diff.changed.length) > 0;

    return (
        <div className="fr-mb-2w" style={{ display: "flex", alignItems: "center", maxWidth: "80vh" }}>
            {displayCheckbox && (
                <input
                    id={`checkbox-${snap.id}`}
                    type="checkbox"
                    checked={selected}
                    onChange={e => onSelect?.(snap.id, e.target.checked)}
                    style={{ marginTop: "0.5rem" }}
                />
            )}
            <div style={{ flex: 1 }}>
                <Accordion label={title}>
                    {hasDiff && (
                        <div className="fr-mb-2w">
                            <p className="fr-text--sm"><strong>Différences vs dernière version</strong></p>
                            <ul className="fr-pl-2w fr-text--sm">
                                <li>Ajouts: {diff!.added.length}</li>
                                <li>Suppressions: {diff!.removed.length}</li>
                                <li>Modifications: {diff!.changed.length}</li>
                            </ul>
                        </div>
                    )}

                    {("data" in snap && (snap as any).data) && (
                        <pre className="fr-text--xs" aria-label="Snapshot JSON">
                            {JSON.stringify((snap as any).data, null, 2)}
                        </pre>
                    )}
                </Accordion>
            </div>
        </div>
    );
}


export function DatasetDetailsModal(props: DatasetDetailsModalProps): JSX.Element {
    const { dataset, platformName, platformUrl } = props;
    const [loadingVersions, setLoadingVersions] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [versions, setVersions] = useState<SnapshotVersion[] | null>(null);
    const [versionsDatasetId, setVersionsDatasetId] = useState<string | null>(null);
    const [selectedSnapshots, setSelectedSnapshots] = useState<Set<string>>(new Set());
    const [renderKey, setRenderKey] = useState(0);

    useEffect(() => {
        setRenderKey(r => r + 1);
    }, [dataset?.id]);

    useEffect(() => {
        setSelectedSnapshots(new Set());
    }, [dataset?.id]);

    const toggleSnapshotSelection = (id: string, checked: boolean) => {
        setSelectedSnapshots(prev => {
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
                const res = await getDatasetVersions(dataset.id, { page: 1, pageSize: 10, includeData: true });
                if (active) setVersions(res.items);
            } catch (e: any) {
                if (active) setError(e?.message ?? "Impossible de charger l'historique");
            } finally {
                if (active) setLoadingVersions(false);
            }
        })();

        return () => { active = false; };
    }, [dataset?.id]);

    const baseline = useMemo<SnapshotVersion | null>(() => {
        if (dataset?.currentSnapshot) return dataset.currentSnapshot;
        if (versionsDatasetId === dataset?.id && versions && versions.length > 0) return versions[0];
        return null;
    }, [dataset?.currentSnapshot, dataset?.id, versions, versionsDatasetId]);

    return (
        <datasetDetailsModal.Component title={dataset?.slug ?? "Détails du dataset"} size="lg" style={{minWidth: "85%"}}>

            {!dataset ? (
                <p className="fr-text">Chargement…</p>
            ) : (
                <>
                    {error && <Alert severity="error" title="Erreur" description={error} className="fr-mb-2w" />}
                    <div className="fr-mb-3w">
                        <p className="fr-text--sm">
                            <strong>Plateforme:</strong>{" "}
                            {platformName ? (
                                platformUrl ? (
                                    <a className="fr-link" href={platformUrl} target="_blank" rel="noreferrer">{platformName}</a>
                                ) : platformName
                            ) : dataset.platformId}
                        </p>
                        <p className="fr-text--sm"><strong>Producteur:</strong> {dataset.publisher ?? "—"}</p>
                        <p className="fr-text--sm"><strong>Créé le:</strong> {new Date(dataset.created).toLocaleString()}</p>
                        <p className="fr-text--sm"><strong>Modifié le:</strong> {new Date(dataset.modified).toLocaleString()}</p>
                        <a className="fr-link" href={dataset.page} target="_blank" rel="noreferrer">Voir sur la plateforme</a>
                    </div>

                    {dataset.currentSnapshot && (
                        <div className="fr-mb-2w">
                            <h6 className="fr-h6">Snapshot courant</h6>
                            <SnapshotItem snap={dataset.currentSnapshot} />
                        </div>
                    )}

                    {Array.isArray(versions) && versionsDatasetId === dataset.id && versions.length > 0 && (
                        <div className="fr-mt-4w">
                            <div className="fr-grid-row fr-grid-row--middle fr-grid-row--gutters fr-mb-2w">
                                <div className="fr-col">
                                    <h6 className="fr-h6 fr-mb-0">Historique des snapshots</h6>
                                </div>
                                {selectedSnapshots.size === 2 && (
                                    <div className="fr-col-auto">
                                        <Button
                                            iconId="ri-git-compare-line"
                                            onClick={() => {
                                                const [aId, bId] = Array.from(selectedSnapshots);
                                                const snapA = versions?.find(v => v.id === aId);
                                                const snapB = versions?.find(v => v.id === bId);
                                                if (snapA && snapB) compareSnapshotsModal.open();
                                            }}
                                        >
                                            Comparer
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
                                                const res = await getDatasetVersions(dataset.id, { page: 1, pageSize: 10, includeData: true });
                                                setVersions(res.items);
                                            } catch (e: any) {
                                                setError(e?.message ?? "Impossible de charger l'historique");
                                            } finally {
                                                setLoadingVersions(false);
                                            }
                                        }}
                                    >
                                        {loadingVersions ? "Chargement…" : "Charger l'historique"}
                                    </Button>
                                </div>
                            </div>

                            {(() => {
                                const [aId, bId] = Array.from(selectedSnapshots);
                                const snapA = versions?.find(v => v.id === aId);
                                const snapB = versions?.find(v => v.id === bId);
                                if (!snapA || !snapB) return null;
                                const comparisonKey = `${snapA.id}-${snapB.id}`;
                                return <CompareSnapshotsModal key={comparisonKey} snapshotA={snapA} snapshotB={snapB} />;
                            })()}

                            {versions.map(s => (
                                <SnapshotItem
                                    key={s.id}
                                    snap={s}
                                    diff={baseline ? computeDiff(baseline.data, s.data) : undefined}
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
    );
}
