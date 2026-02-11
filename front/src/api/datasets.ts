import api from "./api";
import type {
    DatasetDetail,
    DatasetListQuery,
    PaginatedResponse,
    PlatformRef,
    PublishersRef,
    DatasetSummary,
    SnapshotVersion
} from "../types/datasets";

type PaginatedSnake<T> = {
    items: T[];
    total: number;
    page: number;
    page_size: number;
};

export async function getDatasets(query: DatasetListQuery = {}): Promise<{ total: number; pageSize: number; page: number; items: (DatasetSummary & { platformName?: string })[] }> {
    const {
        platformId,
        publisher,
        createdFrom,
        createdTo,
        modifiedFrom,
        modifiedTo,
        q,
        isDeleted,
        sortBy = "modified",
        order = "desc",
        page = 1,
        pageSize = 25
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
        sort_by: sortBy,
        order,
        page,
        page_size: pageSize,
        include_counts: true
    };

    const data = await api.get<{ datasets: any[]; total_datasets: number; page: number; page_size: number }>("/datasets", apiQuery);
    const items: (DatasetSummary & { platformName?: string })[] = (data.datasets ?? []).map((it: any) => ({
        id: it.id,
        platformId: it.platform_id,
        platformName: it.platform_name,
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
        hasDescription: it.has_description,
        isDeleted: it.deleted ?? null,
        quality: it.quality
    }));
    return { items, total: data.total_datasets ?? 0, page: data.page ?? page, pageSize: data.page_size ?? pageSize };
}

export async function getPlatforms(): Promise<PlatformRef[]> {
    const data = await api.get<{ platforms: any[]; total_platforms: number }>("/platforms");
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
        syncs: p.syncs
    }));
}

export async function getPublishers(params?: { platformId?: string; q?: string; limit?: number }): Promise<PublishersRef> {
    const query = {
        platform_id: params?.platformId,
        q: params?.q,
        limit: params?.limit ?? 50
    };
    const data = await api.get<{ items: string[] }>("/publishers", query);
    return data.items ?? [];
}

export async function getDatasetDetail(id: string, includeSnapshots = false): Promise<DatasetDetail> {
    const data = await api.get<any>(`/datasets/${id}`, { include_snapshots: includeSnapshots });
    const mapSnap = (s: any): SnapshotVersion => ({
        id: s.id,
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
        diff: s.diff
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
        currentSnapshot: data.current_snapshot ? mapSnap(data.current_snapshot) : null,
        snapshots: Array.isArray(data.snapshots) ? data.snapshots.map(mapSnap) : undefined,
        hasDescription: data.has_description,
        isDeleted: data.deleted ?? null,
        quality: data.quality
    };
}

export async function getDatasetVersions(id: string, params?: { page?: number; pageSize?: number; includeData?: boolean }): Promise<PaginatedResponse<SnapshotVersion>> {
    const query = {
        page: params?.page ?? 1,
        page_size: params?.pageSize ?? 10,
        include_data: params?.includeData ?? false
    };
    const data = await api.get<{ versions: any[]; total_versions: number; page: number; page_size: number }>(`/datasets/${id}/versions`, query);
    const items: SnapshotVersion[] = (data.versions ?? []).map((s: any) => ({
        id: s.id,
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
        diff: s.diff
    }));

    return { items, total: data.total_versions ?? 0, page: data.page ?? query.page, pageSize: data.page_size ?? query.page_size }
}
export async function evaluateDataset(id: string): Promise<any> {
    const data = await api.post<any>(`/datasets/${id}/evaluate`, {});
    return data;
}

export async function syncDatasetFromSource(url: string): Promise<any> {
    return api.post<any>(`/datasets/add?url=${encodeURIComponent(url)}`, {});
}
