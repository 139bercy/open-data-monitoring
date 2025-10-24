import api from "./api";
import type {
    DatasetDetail,
    DatasetListQuery,
    DatasetSummary,
    PaginatedResponse,
    PlatformRef,
    PublishersRef,
    SnapshotVersion
} from "../types/datasets";

type PaginatedSnake<T> = {
    items: T[];
    total: number;
    page: number;
    page_size: number;
};

export async function getDatasets(query: DatasetListQuery = {}): Promise<PaginatedResponse<DatasetSummary>> {
    const {
        platformId,
        publisher,
        createdFrom,
        createdTo,
        modifiedFrom,
        modifiedTo,
        q,
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
        sort_by: sortBy,
        order,
        page,
        page_size: pageSize,
        include_counts: true
    };

    const data = await api.get<PaginatedSnake<any>>("/datasets", apiQuery);
    const items: DatasetSummary[] = (data.items ?? []).map((it: any) => ({
        id: it.id,
        platformId: it.platform_id,
        platformName: it.platform_name,
        publisher: it.publisher ?? null,
        title: it.title ?? null,
        created: it.created,
        modified: it.modified,
        downloadsCount: it.downloads_count,
        apiCallsCount: it.api_calls_count,
        versionsCount: it.versions_count,
        page: it.page
    }));
    return { items, total: data.total ?? 0, page: data.page ?? page, pageSize: data.page_size ?? pageSize };
}

export async function getPlatforms(): Promise<PlatformRef[]> {
    const data = await api.get<any>("/platforms");
    console.log(data)
    const array = Array.isArray(data?.items)
        ? data.items
        : Array.isArray(data?.platforms)
            ? data.platforms
            : [];
    return array.map((p: any) => ({ id: p.id, name: p.name, created: p.created_at, slug: p.slug, type: p.type, url: p.url, key: p.key, lastSync: p.last_sync, datasetsCount: p.datasets_count }));
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
        page: s.page,
        title: s.title ?? null,
        data: s.data
    });
    return {
        id: data.id,
        platformId: data.platform_id,
        publisher: data.publisher ?? null,
        buid: data.buid,
        slug: data.slug,
        page: data.page,
        created: data.created,
        modified: data.modified,
        published: data.published ?? null,
        restricted: data.restricted ?? null,
        currentSnapshot: data.current_snapshot ? mapSnap(data.current_snapshot) : null,
        snapshots: Array.isArray(data.snapshots) ? data.snapshots.map(mapSnap) : undefined
    };
}

export async function getDatasetVersions(id: string, params?: { page?: number; pageSize?: number; includeData?: boolean }): Promise<PaginatedResponse<SnapshotVersion>> {
    const query = {
        page: params?.page ?? 1,
        page_size: params?.pageSize ?? 10,
        include_data: params?.includeData ?? false
    };
    const data = await api.get<PaginatedSnake<any>>(`/datasets/${id}/versions`, query);
    const items: SnapshotVersion[] = (data.items ?? []).map((s: any) => ({
        id: s.id,
        timestamp: s.timestamp,
        downloadsCount: s.downloads_count ?? null,
        apiCallsCount: s.api_calls_count ?? null,
        page: s.page,
        title: s.title ?? null,
        data: s.data
    }));
    return {items, total: data.total ?? 0, page: data.page ?? query.page, pageSize: data.page_size ?? query.page_size}
}


