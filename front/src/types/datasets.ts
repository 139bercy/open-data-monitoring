export type DatasetSummary = {
    id: string;
    platformId: string;
    platformName?: string;
    publisher: string | null;
    title: string | null;
    created: string;     // ISO8601
    modified: string;    // ISO8601
    downloadsCount?: number;  // present if include_counts=true
    apiCallsCount?: number;   // present if include_counts=true
    versionsCount?: number;   // number of versions (dataset_versions)
    page: string;        // source link
};

export type SnapshotVersion = {
    id: string;
    timestamp: string;         // ISO8601
    downloadsCount: number | null;
    apiCallsCount: number | null;
    page: string;
    title?: string | null;
    data?: unknown;            // only when include_data=true
};

export type DatasetDetail = {
    id: string;
    platformId: string;
    publisher: string | null;
    buid: string;
    slug: string;
    page: string;
    created: string;
    modified: string;
    published: boolean | null;
    restricted: boolean | null;
    currentSnapshot: SnapshotVersion | null;
    snapshots?: SnapshotVersion[] | null; // only when include_snapshots=true
};

export type PaginatedResponse<T> = {
    items: T[];
    total: number;
    page: number;
    pageSize: number;
};

export type DatasetListQuery = {
    platformId?: string;
    publisher?: string;
    createdFrom?: string;
    createdTo?: string;
    modifiedFrom?: string;
    modifiedTo?: string;
    q?: string; // search on slug only
    sortBy?: 'created' | 'modified' | 'publisher' | 'downloads_count' | 'api_calls_count' | 'title' | 'versions_count';
    order?: 'asc' | 'desc';
    page?: number;
    pageSize?: number;
};

export type PlatformRef = {
    id: string;
    name: string;
    created: string;  // ISO8601
    slug: string;
    type: string;
    url: string;
    key: string;
    lastSync: string
};

export type PublishersRef = string[];


