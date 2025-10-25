import { useEffect, useMemo, useState } from "react";
import { Alert } from "@codegouvfr/react-dsfr/Alert";
import { Button } from "@codegouvfr/react-dsfr/Button";
import { DatasetFilters } from "../components/DatasetFilters";
import { DatasetTable } from "../components/DatasetTable";
import {
  DatasetDetailsModal,
  datasetDetailsModal,
} from "../components/DatasetDetailsModal";
import type {
  DatasetDetail,
  DatasetListQuery,
  DatasetSummary,
  PaginatedResponse,
  PlatformRef,
  PublishersRef,
} from "../types/datasets";
import {
  getDatasets,
  getPlatforms,
  getPublishers,
  getDatasetDetail,
} from "../api/datasets";

export function DatasetListPage(): JSX.Element {
  const [query, setQuery] = useState<DatasetListQuery>({
    page: 1,
    pageSize: 25,
    sortBy: "modified",
    order: "desc",
  });
  const [data, setData] = useState<PaginatedResponse<DatasetSummary>>({
    items: [],
    total: 0,
    page: 1,
    pageSize: 25,
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [platforms, setPlatforms] = useState<PlatformRef[]>([]);
  const [publishers, setPublishers] = useState<PublishersRef>([]);

  const [selected, setSelected] = useState<DatasetDetail | null>(null);

  // load ref data once (platforms)
  useEffect(() => {
    getPlatforms()
      .then(setPlatforms)
      .catch(() => undefined);
  }, []);

  // reload publishers when platform changes (basic)
  useEffect(() => {
    const platformId = query.platformId;
    getPublishers({ platformId, limit: 200 })
      .then(setPublishers)
      .catch(() => setPublishers([]));
  }, [query.platformId]);

  // datasets list
  useEffect(() => {
    let aborted = false;
    setLoading(true);
    setError(null);
    getDatasets(query)
      .then((res) => {
        if (aborted) return;
        setData(res);
        // Clamp page if out of range after filters/sort/pageSize changes
        const totalPages = Math.max(
          1,
          Math.ceil((res.total ?? 0) / Math.max(1, query.pageSize ?? 25))
        );
        if (res.total > 0 && (query.page ?? 1) > totalPages) {
          // Move to last available page to avoid empty table
          setQuery((q) => ({ ...q, page: totalPages }));
        }
      })
      .catch((err) => {
        if (aborted) return;
        setError(err.message ?? "Erreur inconnue");
      })
      .finally(() => {
        if (aborted) return;
        setLoading(false);
      });
    return () => {
      aborted = true;
    };
  }, [
    query.page,
    query.pageSize,
    query.sortBy,
    query.order,
    query.platformId,
    query.publisher,
    query.createdFrom,
    query.createdTo,
    query.modifiedFrom,
    query.modifiedTo,
    query.q,
  ]);

  const handleOpenDetails = async (datasetId: string) => {
    try {
      // reset previous selection to avoid stale content flash
      setSelected(null);
      const detail = await getDatasetDetail(datasetId, false);
      setSelected(detail);
      datasetDetailsModal.open();
    } catch {
      // ignore for now
    }
  };

  const resetFilters = () => {
    setQuery({
      page: 1,
      pageSize: query.pageSize,
      sortBy: "modified",
      order: "desc",
    });
  };

  const title = useMemo(() => "Jeux de données", []);

  // Resolve platform_id -> platform name for display
  const platformNameById = useMemo(() => {
    const map = new Map<string, string>();
    platforms.forEach((p) => map.set(p.id, p.name ?? p.slug));
    return map;
  }, [platforms]);

  const displayItems = useMemo(() => {
    return data.items.map((it) => ({
      ...it,
      platformName: platformNameById.get(it.platformId) ?? it.platformName,
    }));
  }, [data.items, platformNameById]);

  return (
    <div className="fr-container fr-my-6w">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h1 className="fr-h1">{title}</h1>
        <nav
          className="fr-breadcrumb"
          aria-label="fil d’Ariane"
        >
          <ol className="fr-breadcrumb__list">
            <li className="fr-breadcrumb__item">
              <a
                className="fr-breadcrumb__link"
                href="/"
              >
                Accueil
              </a>
            </li>
            <li
              className="fr-breadcrumb__item"
              aria-current="page"
            >
              Jeux de données
            </li>
          </ol>
        </nav>
      </div>

      <DatasetFilters
        query={query}
        platforms={platforms}
        publishers={publishers}
        onChange={(partial) => setQuery((q) => ({ ...q, ...partial }))}
        onReset={resetFilters}
      />

      {error && (
        <Alert
          severity="error"
          title="Erreur"
          description={error}
          className="fr-mb-3w"
        />
      )}

      <DatasetTable
        loading={loading}
        items={displayItems}
        total={data.total}
        page={query.page ?? data.page}
        pageSize={query.pageSize ?? data.pageSize}
        sortBy={query.sortBy}
        order={query.order}
        onSortChange={(sortBy, order) =>
          setQuery((q) => ({ ...q, sortBy, order, page: 1 }))
        }
        onPageChange={(p) => setQuery((q) => ({ ...q, page: p }))}
        onPageSizeChange={(size) =>
          setQuery((q) => ({ ...q, page: 1, pageSize: size }))
        }
        onRowClick={handleOpenDetails}
        style={{ width: "100%" }}
      />

      <DatasetDetailsModal
        dataset={selected}
        platformName={
          selected ? (platformNameById.get(selected.platformId) ?? null) : null
        }
        platformUrl={selected?.page ? new URL(selected.page).origin : null}
      />
      <div className="fr-mt-6w">
        <Button
          priority="tertiary no outline"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        >
          Revenir en haut de page
        </Button>
      </div>
    </div>
  );
}
