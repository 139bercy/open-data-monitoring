import { useMemo } from "react";
import { Table } from "@codegouvfr/react-dsfr/Table";
import { Select } from "@codegouvfr/react-dsfr/Select";
import { PaginationDsfr } from "./PaginationDsfr";
import { Alert } from "@codegouvfr/react-dsfr/Alert";
import type { DatasetSummary, DatasetListQuery } from "../types/datasets";

export type DatasetTableProps = Readonly<{
  items: DatasetSummary[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
  onRowClick?: (datasetId: string) => void;
  sortBy?: DatasetListQuery["sortBy"];
  order?: DatasetListQuery["order"];
  onSortChange?: (
    sortBy: NonNullable<DatasetListQuery["sortBy"]>,
    order: NonNullable<DatasetListQuery["order"]>
  ) => void;
  loading?: boolean;
  skeletonRowCount?: number;
}>;

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString();
  } catch {
    return iso;
  }
}

function handlePageChange(
  e: React.MouseEvent<HTMLAnchorElement>,
  pageNumber: number,
  onPageChange?: (page: number) => void
): void {
  e.preventDefault();
  onPageChange?.(pageNumber);
}

function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  try {
    return Number(value).toLocaleString("fr-FR");
  } catch {
    return String(value);
  }
}

export function DatasetTable(props: DatasetTableProps): JSX.Element {
  const {
    items,
    total,
    page,
    pageSize,
    onPageChange,
    onRowClick,
    loading,
    skeletonRowCount,
  } = props;
  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(total / Math.max(1, pageSize))),
    [total, pageSize]
  );

  console.log(items);

  const skeletonRows = useMemo(() => {
    const count = Math.max(1, skeletonRowCount ?? Math.min(10, pageSize || 10));
    return Array.from({ length: count }, (_, i) => [
      <span
        key={`sk-status-${i}`}
        className="fr-skeleton fr-skeleton--text"
        aria-hidden="true"
      />,
      <span
        key={`sk-title-${i}`}
        className="fr-skeleton fr-skeleton--text"
        aria-hidden="true"
      />,
      <span
        key={`sk-platform-${i}`}
        className="fr-skeleton fr-skeleton--text"
        aria-hidden="true"
      />,
      <span
        key={`sk-publisher-${i}`}
        className="fr-skeleton fr-skeleton--text"
        aria-hidden="true"
      />,
      <span
        key={`sk-created-${i}`}
        className="fr-skeleton fr-skeleton--text"
        aria-hidden="true"
      />,
      <span
        key={`sk-modified-${i}`}
        className="fr-skeleton fr-skeleton--text"
        aria-hidden="true"
      />,
      <span
        key={`sk-api-${i}`}
        className="fr-skeleton fr-skeleton--text"
        aria-hidden="true"
      />,
      <span
        key={`sk-dl-${i}`}
        className="fr-skeleton fr-skeleton--text"
        aria-hidden="true"
      />,
      <span
        key={`sk-ver-${i}`}
        className="fr-skeleton fr-skeleton--text"
        aria-hidden="true"
      />,
      <span
        key={`sk-action-${i}`}
        className="fr-skeleton"
        style={{ width: 64, height: 32 }}
        aria-hidden="true"
      />,
    ]);
  }, [skeletonRowCount, pageSize]);

  if (!loading && items.length === 0) {
    return (
      <Alert
        severity="info"
        title="Aucun jeu de données"
        description="Modifiez les critères ou réessayez plus tard."
        className="fr-my-4w"
      />
    );
  }

  return (
    <div
      className="fr-my-1w"
      style={{ width: "100%" }}
      aria-busy={!!loading}
      aria-live="polite"
    >
      <Table
        caption="Liste des jeux de données"
        headers={[
          "Statut",
          <button
            key="h-title"
            className="fr-btn fr-btn--tertiary-no-outline fr-btn--sm"
            type="button"
            disabled={!!loading}
            onClick={() => {
              const nextOrder =
                props.order === "asc" && props.sortBy === "title"
                  ? "desc"
                  : "asc";
              props.onSortChange?.("title", nextOrder as "asc" | "desc");
            }}
            aria-pressed={props.sortBy === "title"}
            aria-label="Trier par titre"
          >
            Titre{" "}
            {props.sortBy === "title"
              ? props.order === "asc"
                ? "▲"
                : "▼"
              : ""}
          </button>,
          "Plateforme",
          "Producteur",
          <button
            key="h-created"
            className="fr-btn fr-btn--tertiary-no-outline fr-btn--sm"
            type="button"
            disabled={!!loading}
            onClick={() => {
              const nextOrder =
                props.order === "asc" && props.sortBy === "created"
                  ? "desc"
                  : "asc";
              props.onSortChange?.("created", nextOrder as "asc" | "desc");
            }}
            aria-pressed={props.sortBy === "created"}
            aria-label="Trier par créé le"
          >
            Créé le{" "}
            {props.sortBy === "created"
              ? props.order === "asc"
                ? "▲"
                : "▼"
              : ""}
          </button>,
          <button
            key="h-modified"
            className="fr-btn fr-btn--tertiary-no-outline fr-btn--sm"
            type="button"
            disabled={!!loading}
            onClick={() => {
              const nextOrder =
                props.order === "asc" && props.sortBy === "modified"
                  ? "desc"
                  : "asc";
              props.onSortChange?.("modified", nextOrder as "asc" | "desc");
            }}
            aria-pressed={props.sortBy === "modified"}
            aria-label="Trier par modifié le"
          >
            Modifié le{" "}
            {props.sortBy === "modified"
              ? props.order === "asc"
                ? "▲"
                : "▼"
              : ""}
          </button>,
          <button
            key="h-api"
            className="fr-btn fr-btn--tertiary-no-outline fr-btn--sm"
            type="button"
            disabled={!!loading}
            onClick={() => {
              const nextOrder =
                props.order === "asc" && props.sortBy === "api_calls_count"
                  ? "desc"
                  : "asc";
              props.onSortChange?.(
                "api_calls_count",
                nextOrder as "asc" | "desc"
              );
            }}
            aria-pressed={props.sortBy === "api_calls_count"}
            aria-label="Trier par nb d'appels API"
          >
            API calls{" "}
            {props.sortBy === "api_calls_count"
              ? props.order === "asc"
                ? "▲"
                : "▼"
              : ""}
          </button>,
          <button
            key="h-downloads"
            className="fr-btn fr-btn--tertiary-no-outline fr-btn--sm"
            type="button"
            disabled={!!loading}
            onClick={() => {
              const nextOrder =
                props.order === "asc" && props.sortBy === "downloads_count"
                  ? "desc"
                  : "asc";
              props.onSortChange?.(
                "downloads_count",
                nextOrder as "asc" | "desc"
              );
            }}
            aria-pressed={props.sortBy === "downloads_count"}
            aria-label="Trier par téléchargements"
          >
            Downloads{" "}
            {props.sortBy === "downloads_count"
              ? props.order === "asc"
                ? "▲"
                : "▼"
              : ""}
          </button>,
          <button
            key="h-versions"
            className="fr-btn fr-btn--tertiary-no-outline fr-btn--sm"
            type="button"
            disabled={!!loading}
            onClick={() => {
              const nextOrder =
                props.order === "asc" && props.sortBy === "versions_count"
                  ? "desc"
                  : "asc";
              props.onSortChange?.(
                "versions_count",
                nextOrder as "asc" | "desc"
              );
            }}
            aria-pressed={props.sortBy === "versions_count"}
            aria-label="Trier par nombre de versions"
          >
            Versions{" "}
            {props.sortBy === "versions_count"
              ? props.order === "asc"
                ? "▲"
                : "▼"
              : ""}
          </button>,
          "Action",
        ]}
        data={
          loading
            ? skeletonRows
            : items.map((item) => [
                <div
                  style={{
                    display: "flex",
                    gap: "0.5rem",
                    flexDirection: "column",
                  }}
                >
                  <span
                    className={`fr-badge ${
                      item.lastSyncStatus === "success"
                        ? "fr-badge--success"
                        : item.lastSyncStatus === "pending"
                          ? "fr-badge--info"
                          : "fr-badge--error"
                    }`}
                    style={{
                      minWidth: "4rem",
                      textAlign: "center",
                      alignItems: "center",
                    }}
                  >
                    {item.lastSyncStatus === "success"
                      ? "🟢"
                      : item.lastSyncStatus === "pending"
                        ? "🟡"
                        : "🔴"}{" "}
                  </span>
                  <span
                    className={`fr-badge ${
                      item.published ? "fr-badge--success" : "fr-badge--warning"
                    }`}
                    style={{
                      minWidth: "4rem",
                      textAlign: "center",
                      alignItems: "center",
                    }}
                  >
                    {item.published ? "📢" : "🚧"}
                  </span>
                  <span
                    className={`fr-badge ${
                      item.restricted ? "fr-badge--error" : "fr-badge--success"
                    }`}
                    style={{
                      minWidth: "4rem",
                      textAlign: "center",
                      alignItems: "center",
                    }}
                  >
                    {item.restricted ? "🔒" : "✓"}
                  </span>
                </div>,
                item.title ?? "—",
                item.platformName ?? item.platformId,
                item.publisher ?? "—",
                formatDate(item.created),
                formatDate(item.modified),
                formatNumber(item.apiCallsCount),
                formatNumber(item.downloadsCount),
                formatNumber(item.versionsCount),
                <button
                  key={`view-${item.id}`}
                  className="fr-btn fr-btn--sm"
                  onClick={() => onRowClick?.(item.id)}
                  aria-label={`Voir les détails de ${item.title ?? item.id}`}
                  type="button"
                  style={{ transition: "transform .15s ease" }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLButtonElement).style.transform =
                      "scale(1.02)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLButtonElement).style.transform =
                      "scale(1)";
                  }}
                >
                  Voir
                </button>,
              ])
        }
      />
      {/* Hover effect for table rows using DSFR classes */}
      <style>{`.fr-table table tbody tr{transition:background-color .15s ease}.fr-table table tbody tr:hover{background-color:var(--background-alt-grey)}`}</style>

      <div
        className="fr-grid-row fr-grid-row--middle fr-mt-1w"
        aria-label="Pagination et options"
        style={{
          width: "100%",
          opacity: loading ? 0.6 : 1,
          pointerEvents: loading ? "none" : "auto",
        }}
      >
        <div className="fr-col-auto">
          <div className="fr-grid-row fr-grid-row--middle fr-grid-row--gutters">
            <div className="fr-col-auto">
              <PaginationDsfr
                page={page}
                totalPages={totalPages}
                onPageChange={(p) => onPageChange?.(p)}
              />
            </div>
            <div className="fr-col-auto">
              <Select
                label="Résultats par page"
                nativeSelectProps={{
                  value: String(pageSize),
                  disabled: !!loading,
                  onChange: (e: React.ChangeEvent<HTMLSelectElement>) =>
                    props.onPageSizeChange?.(Number(e.currentTarget.value)),
                  style: { width: "8rem" },
                }}
              >
                {[10, 25, 50, 100].map((size) => (
                  <option
                    key={size}
                    value={size}
                  >
                    {size}
                  </option>
                ))}
              </Select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
