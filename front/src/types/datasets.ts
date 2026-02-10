// ============================================================================
// Dataset Types
// ============================================================================

// ----------------------------------------------------------------------------
// Domain Primitives
// ----------------------------------------------------------------------------

type UUID = string;
type ISO8601Date = string;
type URL = string;

// ----------------------------------------------------------------------------
// Dataset Domain Types
// ----------------------------------------------------------------------------

type Publisher = string | null;
type DatasetTitle = string | null;

type QualityIndicators = {
    has_description: boolean;
    is_slug_valid: boolean;  // No underscores or special chars
    evaluation_results: any | null;  // LLM evaluation results (JSON)
}

// ----------------------------------------------------------------------------
// List View (Table Display)
// ----------------------------------------------------------------------------

export type DatasetSummary = {
    id: UUID;
    platformId: UUID;
    platformName?: string;
    platformType?: string;
    publisher: Publisher;
    title: DatasetTitle;
    created: ISO8601Date;
    modified: ISO8601Date;
    downloadsCount?: number;
    apiCallsCount?: number;
    viewsCount?: number;
    reusesCount?: number;
    followersCount?: number;
    popularityScore?: number;
    versionsCount?: number;
    page: URL;
    restricted: boolean | null;
    published: boolean | null;
    lastSyncStatus: string;
    hasDescription: boolean;
    isDeleted: boolean | null;
    quality?: QualityIndicators;
};

// ----------------------------------------------------------------------------
// Version History
// ----------------------------------------------------------------------------

/**
 * Immutable snapshot of dataset state at a point in time.
 * Backend pre-calculates diffs for performance.
 */
export type SnapshotVersion = {
    id: UUID;
    timestamp: ISO8601Date;
    downloadsCount: number | null;
    apiCallsCount: number | null;
    viewsCount?: number | null;
    reusesCount?: number | null;
    followersCount?: number | null;
    popularityScore?: number | null;
    page: URL;
    title?: DatasetTitle;
    data?: unknown;  // Full snapshot (only when include_data=true)
    diff?: any;  // Pre-calculated by backend
};

// ----------------------------------------------------------------------------
// Detail View (Modal Display)
// ----------------------------------------------------------------------------

export type DatasetDetail = {
    id: UUID;
    platformId: UUID;
    publisher: Publisher;
    title: DatasetTitle;
    buid: string;  // Business UID from source platform
    slug: string;
    page: URL;
    created: ISO8601Date;
    modified: ISO8601Date;
    published: boolean | null;
    restricted: boolean | null;
    hasDescription: boolean;
    isDeleted: boolean | null;
    quality?: QualityIndicators;
    currentSnapshot: SnapshotVersion | null;
    snapshots?: SnapshotVersion[] | null;  // Only when include_snapshots=true
};

// ----------------------------------------------------------------------------
// API Contracts
// ----------------------------------------------------------------------------

export type PaginatedResponse<T> = {
    items: T[];
    total: number;
    page: number;  // 1-indexed
    pageSize: number;
};

export type DatasetListQuery = {
    // Filters
    platformId?: UUID;
    publisher?: string;  // Partial match
    q?: string;  // Searches slug only
    isDeleted?: boolean;

    // Date ranges
    createdFrom?: ISO8601Date;
    createdTo?: ISO8601Date;
    modifiedFrom?: ISO8601Date;
    modifiedTo?: ISO8601Date;

    // Sorting
    sortBy?: 'created' | 'modified' | 'publisher' | 'downloads_count' | 'api_calls_count' | 'title' | 'versions_count' | 'popularity_score' | 'views_count' | 'reuses_count';
    order?: 'asc' | 'desc';

    // Pagination
    page?: number;
    pageSize?: number;
};

// ----------------------------------------------------------------------------
// Publishers
// ----------------------------------------------------------------------------

/**
 * List of all publishers in the system.
 * Used for autocomplete and filtering.
 */
export type PublishersRef = string[];

// ----------------------------------------------------------------------------
// Re-exports
// ----------------------------------------------------------------------------

export type { PlatformRef, PlatformSync } from './platforms';
