import { useCallback, useEffect, useMemo, useState, useRef } from "react";
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
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  getDatasets,
  getPlatforms,
  getPublishers,
  getDatasetDetail,
} from "../api/datasets";

export function DatasetListPage(): JSX.Element {
  const { id: routeId } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [searchParams, setSearchParams] = useSearchParams();

  // Helper to convert URL params to DatasetListQuery
  const getQueryFromParams = useCallback((): DatasetListQuery => {
    return {
      page: Number(searchParams.get("page")) || 1,
      pageSize: Number(searchParams.get("pageSize")) || 25,
      sortBy: (searchParams.get("sortBy") as any) || "modified",
      order: (searchParams.get("order") as any) || "desc",
      q: searchParams.get("q") || undefined,
      platformId: searchParams.get("platformId") || undefined,
      publisher: searchParams.get("publisher") || undefined,
      isDeleted: searchParams.has("isDeleted")
        ? searchParams.get("isDeleted") === "true"
        : undefined,
      createdFrom: searchParams.get("createdFrom") || undefined,
      createdTo: searchParams.get("createdTo") || undefined,
      modifiedFrom: searchParams.get("modifiedFrom") || undefined,
      modifiedTo: searchParams.get("modifiedTo") || undefined,
    };
  }, [searchParams]);

  const [query, setQuery] = useState<DatasetListQuery>(getQueryFromParams());

  // Update URL whenever query state changes
  useEffect(() => {
    const params = new URLSearchParams();
    if (query.page && query.page !== 1) params.set("page", String(query.page));
    if (query.pageSize && query.pageSize !== 25)
      params.set("pageSize", String(query.pageSize));
    if (query.sortBy && query.sortBy !== "modified")
      params.set("sortBy", query.sortBy);
    if (query.order && query.order !== "desc") params.set("order", query.order);
    if (query.q) params.set("q", query.q);
    if (query.platformId) params.set("platformId", query.platformId);
    if (query.publisher) params.set("publisher", query.publisher);
    if (query.isDeleted !== undefined)
      params.set("isDeleted", String(query.isDeleted));
    if (query.createdFrom) params.set("createdFrom", query.createdFrom);
    if (query.createdTo) params.set("createdTo", query.createdTo);
    if (query.modifiedFrom) params.set("modifiedFrom", query.modifiedFrom);
    if (query.modifiedTo) params.set("modifiedTo", query.modifiedTo);

    // Only update if search-params string actually changed to avoid loop
    const newSearchStr = params.toString();
    if (newSearchStr !== searchParams.toString()) {
      setSearchParams(params, { replace: true });
    }
  }, [query, setSearchParams, searchParams]);

  // Update query whenever URL parameters change (for back/forward navigation)
  useEffect(() => {
    const fromUrl = getQueryFromParams();
    // Only update if there's an actual difference to avoid unnecessary refreshes
    if (JSON.stringify(fromUrl) !== JSON.stringify(query)) {
      setQuery(fromUrl);
    }
  }, [searchParams, getQueryFromParams]);
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

  // handle deep link
  useEffect(() => {
    if (routeId) {
      if (!selected || selected.id !== routeId) {
        handleOpenDetails(routeId);
      }
    } else {
      // No ID in URL -> modal should be closed
      if (selected) {
        setSelected(null);
      }
      try {
        datasetDetailsModal.close();
      } catch {}
    }
  }, [routeId, selected?.id]);

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
    query.isDeleted,
  ]);

  const handleOpenDetails = async (datasetId: string) => {
    try {
      // reset previous selection to avoid stale content flash
      setSelected(null);
      const detail = await getDatasetDetail(datasetId, false);
      setSelected(detail);
      datasetDetailsModal.open();
    } catch (err: any) {
      setError(
        `Impossible de charger le détail du jeu de données: ${err.message}`
      );
    }
  };

  const handleClose = useCallback(() => {
    navigate({ pathname: "/datasets/", search: searchParams.toString() });
  }, [navigate, searchParams]);

  const handleNavigateDetail = useCallback(
    (id: string) => {
      navigate({
        pathname: `/datasets/${id}`,
        search: searchParams.toString(),
      });
    },
    [navigate, searchParams]
  );

  const resetFilters = () => {
    setQuery({
      page: 1,
      pageSize: query.pageSize,
      sortBy: "modified",
      order: "desc",
    });
  };

  const title = useMemo(() => "Jeux de données", []);

  // Resolve platform_id -> platform info for display
  const platformInfoById = useMemo(() => {
    const map = new Map<string, PlatformRef>();
    platforms.forEach((p) => map.set(p.id, p));
    return map;
  }, [platforms]);

  const displayItems = useMemo(() => {
    return data.items.map((it) => {
      const p = platformInfoById.get(it.platformId);
      return {
        ...it,
        platformName: p?.name ?? it.platformName,
        platformType: p?.type,
      };
    });
  }, [data.items, platformInfoById]);

  return (
    <div
      className="fr-container fr-my-6w"
      style={{ maxWidth: "70%", paddingLeft: 0, paddingRight: 0 }}
    >
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
        onChange={(partial) => {
          setQuery((q) => {
            const next = { ...q, ...partial };
            // If query text changed, don't reset page immediately to avoid jumpy UI,
            // but we usually want page 1 on filter changes.
            return next;
          });
        }}
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
        onRowClick={(id) => handleNavigateDetail(id)}
      />

      <DatasetDetailsModal
        dataset={selected}
        platformName={
          selected
            ? (platformInfoById.get(selected.platformId)?.name ?? null)
            : null
        }
        platformUrl={(() => {
          if (!selected?.page) return null;
          try {
            return new URL(selected.page).origin;
          } catch {
            return null;
          }
        })()}
        onNavigate={handleNavigateDetail}
        onClose={handleClose}
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
