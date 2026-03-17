import api from "./api";
import type {
  DatasetDetail,
  DatasetListQuery,
  PaginatedResponse,
  PlatformRef,
  PublishersRef,
  DatasetSummary,
  SnapshotVersion,
} from "../types/datasets";

type PaginatedSnake<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export async function getDatasets(
  query: DatasetListQuery = {}
): Promise<{
  total: number;
  pageSize: number;
  page: number;
  items: (DatasetSummary & { platformName?: string })[];
}> {
  const {
    platformId,
    publisher,
    createdFrom,
    createdTo,
    modifiedFrom,
    modifiedTo,
    q,
    isDeleted,
    minHealth,
    maxHealth,
    sortBy = "modified",
    order = "desc",
    page = 1,
    pageSize = 25,
    includeColdStorage = false,
  } = query;

  const apiQuery: Record<string, unknown> = {
    platform_id: platformId,
    publisher,
    created_from: createdFrom,
    created_to: createdTo,
    modified_from: modifiedFrom,
    modified_to: modifiedTo,
    q,
    is_deleted: isDeleted,
    include_cold_storage: includeColdStorage,
    min_health: minHealth,
    max_health: maxHealth,
    sort_by: sortBy,
    order,
    page,
    page_size: pageSize,
    include_counts: true,
  };

  const data = await api.get<{
    datasets: any[];
    total_datasets: number;
    page: number;
    page_size: number;
  }>("/datasets", apiQuery);
  const items: (DatasetSummary & { platformName?: string })[] = (
    data.datasets ?? []
  ).map((it: any) => ({
    id: it.id,
    platformId: it.platform_id,
    platformName: it.platform_name,
    slug: it.slug,
    publisher: it.publisher ?? null,
    title: it.title ?? null,
    created: it.created,
    modified: it.modified,
    downloadsCount: it.downloads_count,
    apiCallsCount: it.api_calls_count,
    viewsCount: it.views_count,
    reusesCount: it.reuses_count,
    followersCount: it.followers_count,
    popularityScore: it.popularity_score,
    versionsCount: it.versions_count,
    page: it.page,

    restricted: it.restricted ?? null,
    published: it.published ?? null,
    lastSync: it.last_sync,
    lastSyncStatus: it.last_sync_status,
    hasDescription: it.quality?.has_description ?? false,
    isDeleted: it.deleted ?? null,
    deletedAt: it.deleted_at ?? null,
    linkedDatasetId: it.linked_dataset_id,
    linkedDatasetSlug: it.linked_dataset_slug,
    linkedPlatformName: it.linked_platform_name,
    quality: it.quality,
    healthScore: it.health_score,
    healthQualityScore: it.health_quality_score,
    healthFreshnessScore: it.health_freshness_score,
    healthEngagementScore: it.health_engagement_score,
  }));
  return {
    items,
    total: data.total_datasets ?? 0,
    page: data.page ?? page,
    pageSize: data.page_size ?? pageSize,
  };
}

export async function getPlatforms(): Promise<PlatformRef[]> {
  const data = await api.get<{ platforms: any[]; total_platforms: number }>(
    "/platforms"
  );
  return (data.platforms ?? []).map((p: any) => ({
    id: p.id,
    name: p.name,
    created: p.created_at,
    slug: p.slug,
    type: p.type,
    url: p.url,
    key: p.key,
    lastSync: p.last_sync,
    lastSyncStatus: p.last_sync_status,
    datasetsCount: p.datasets_count,
    syncs: p.syncs,
  }));
}

export async function getPublishers(params?: {
  platformId?: string;
  q?: string;
  limit?: number;
}): Promise<PublishersRef> {
  const query = {
    platform_id: params?.platformId,
    q: params?.q,
    limit: params?.limit ?? 50,
  };
  const data = await api.get<{ items: string[] }>("/publishers", query);
  return data.items ?? [];
}

export async function getDatasetDetail(
  id: string,
  includeSnapshots = false
): Promise<DatasetDetail> {
  const data = await api.get<any>(`/datasets/${id}`, {
    include_snapshots: includeSnapshots,
  });
  const mapSnap = (s: any): SnapshotVersion => ({
    id: s.id,
    blob_id: s.blob_id,
    timestamp: s.timestamp,
    downloadsCount: s.downloads_count ?? null,
    apiCallsCount: s.api_calls_count ?? null,
    viewsCount: s.views_count ?? null,
    reusesCount: s.reuses_count ?? null,
    followersCount: s.followers_count ?? null,
    popularityScore: s.popularity_score ?? null,
    page: s.page,
    title: s.title ?? null,
    data: s.data,
    diff: s.diff,
  });

  return {
    id: data.id,
    platformId: data.platform_id,
    publisher: data.publisher ?? null,
    title: data.title ?? null,
    buid: data.buid,
    slug: data.slug,
    page: data.page,
    created: data.created,
    modified: data.modified,
    published: data.published ?? null,
    restricted: data.restricted ?? null,
    currentSnapshot: data.current_snapshot
      ? mapSnap(data.current_snapshot)
      : null,
    snapshots: Array.isArray(data.snapshots)
      ? data.snapshots.map(mapSnap)
      : undefined,
    hasDescription: data.quality?.has_description ?? false,
    isDeleted: data.deleted ?? null,
    deletedAt: data.deleted_at ?? null,
    linkedDatasetId: data.linked_dataset_id,
    linkedDatasetSlug: data.linked_dataset_slug,
    linkedPlatformName: data.linked_platform_name,
    quality: data.quality,
    healthScore: data.health_score,
    healthBreakdown: data.health_breakdown,
  };
}

export async function getDatasetVersions(
  id: string,
  params?: { page?: number; pageSize?: number; includeData?: boolean }
): Promise<PaginatedResponse<SnapshotVersion>> {
  const query = {
    page: params?.page ?? 1,
    page_size: params?.pageSize ?? 10,
    include_data: params?.includeData ?? false,
  };
  const data = await api.get<{
    versions: any[];
    total_versions: number;
    page: number;
    page_size: number;
  }>(`/datasets/${id}/versions`, query);
  const items: SnapshotVersion[] = (data.versions ?? []).map((s: any) => ({
    id: s.id,
    blob_id: s.blob_id,
    timestamp: s.timestamp,
    downloadsCount: s.downloads_count ?? null,
    apiCallsCount: s.api_calls_count ?? null,
    viewsCount: s.views_count ?? null,
    reusesCount: s.reuses_count ?? null,
    followersCount: s.followers_count ?? null,
    popularityScore: s.popularity_score ?? null,
    page: s.page,
    title: s.title ?? null,
    data: s.data,
    diff: s.diff,
  }));

  return {
    items,
    total: data.total_versions ?? 0,
    page: data.page ?? query.page,
    pageSize: data.page_size ?? query.page_size,
  };
}
export async function evaluateDataset(id: string): Promise<any> {
  const data = await api.post<any>(`/datasets/${id}/evaluate`, {});
  return data;
}

export async function syncDatasetFromSource(url: string): Promise<any> {
  return api.post<any>(`/datasets/add?url=${encodeURIComponent(url)}`, {});
}

export async function downloadAuditReport(
  id: string,
  slug: string
): Promise<void> {
  const blob = await api.getBlob(`/datasets/${id}/audit-report`);

  // Trigger download in browser
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `audit-report-${slug}.pdf`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
