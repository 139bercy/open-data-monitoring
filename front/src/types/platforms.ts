// ============================================================================
// Platform Types
// ============================================================================

// ----------------------------------------------------------------------------
// Domain Primitives
// ----------------------------------------------------------------------------

type UUID = string;
type ISO8601Date = string;
type URL = string;
type PlatformSlug = string;
type APIKey = string;

// ----------------------------------------------------------------------------
// Platform Types
// ----------------------------------------------------------------------------

/**
 * Platform type determines which adapter to use for data extraction.
 * Each type has its own API contract and data structure.
 */
type PlatformType = 'opendatasoft' | 'datagouv' | string;

type SyncStatus = 'pending' | 'success' | 'failed';

// ----------------------------------------------------------------------------
// Sync History
// ----------------------------------------------------------------------------

/**
 * Record of a single synchronization execution.
 * Tracks when sync ran, its outcome, and how many datasets were processed.
 */
export type PlatformSync = {
    id: UUID;
    platform_id: UUID;
    timestamp: ISO8601Date;
    status: SyncStatus;
    datasets_count: number;
}

// ----------------------------------------------------------------------------
// Platform Reference
// ----------------------------------------------------------------------------

/**
 * Complete platform configuration and state.
 * Used for platform management and monitoring.
 */
export type PlatformRef = {
    id: UUID;
    name: string;
    slug: PlatformSlug;
    type: PlatformType;
    url: URL;
    key: APIKey;  // Masked on client side
    created: ISO8601Date;
    lastSync: ISO8601Date;
    lastSyncStatus: SyncStatus;
    datasetsCount: number;
    syncs?: PlatformSync[];  // Full sync history (optional)
};
