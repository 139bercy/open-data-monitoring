/**
 * API Client Tests - Characterization approach
 *
 * Using Feathers' "Seams" technique:
 * MSW intercepts at the HTTP boundary, allowing us to test without modifying production code
 */

import { describe, it, expect } from 'vitest';
import { server, setupMSW, http, HttpResponse } from './setup';
import { getDatasets, getPlatforms, getPublishers } from '../../api/datasets';

describe('API Client - Characterization Tests', () => {
    setupMSW();

    describe('getDatasets', () => {
        it('should transform snake_case API response to camelCase', async () => {
            server.use(
                http.get('/api/datasets', () => {
                    return HttpResponse.json({
                        datasets: [
                            {
                                id: 'test-id',
                                platform_id: 'platform-1',
                                platform_name: 'Test Platform',
                                title: 'Test Dataset',
                                page: 'https://test.com',
                                created: '2024-01-01T00:00:00Z',
                                modified: '2024-01-01T00:00:00Z',
                                downloads_count: 100,
                                api_calls_count: 50,
                                views_count: 1000,
                                reuses_count: 5,
                                followers_count: 10,
                                popularity_score: 75.5,
                                versions_count: 3,
                                last_sync_status: 'success',
                                deleted: false,
                            },
                        ],
                        total_datasets: 1,
                        page: 1,
                        page_size: 25,
                    });
                })
            );

            const result = await getDatasets();

            // Characterization: Documents current transformation behavior
            expect(result.items[0]).toMatchObject({
                id: 'test-id',
                platformId: 'platform-1',
                platformName: 'Test Platform',
                downloadsCount: 100,
                apiCallsCount: 50,
                viewsCount: 1000,
                reusesCount: 5,
                followersCount: 10,
                popularityScore: 75.5,
                versionsCount: 3,
                lastSyncStatus: 'success',
                isDeleted: false,
            });
        });

        it('should handle null values correctly', async () => {
            server.use(
                http.get('/api/datasets', () => {
                    return HttpResponse.json({
                        datasets: [
                            {
                                id: 'test-id',
                                platform_id: 'platform-1',
                                title: null,
                                publisher: null,
                                downloads_count: null,
                                api_calls_count: null,
                                page: 'https://test.com',
                                created: '2024-01-01T00:00:00Z',
                                modified: '2024-01-01T00:00:00Z',
                            },
                        ],
                        total_datasets: 1,
                    });
                })
            );

            const result = await getDatasets();

            // Characterization: null values pass through
            expect(result.items[0].title).toBeNull();
            expect(result.items[0].publisher).toBeNull();
            expect(result.items[0].downloadsCount).toBeNull();
            expect(result.items[0].apiCallsCount).toBeNull();
        });

        it('should apply default query parameters', async () => {
            let capturedUrl: string | undefined;

            server.use(
                http.get('/api/datasets', ({ request }) => {
                    capturedUrl = request.url;
                    return HttpResponse.json({
                        datasets: [],
                        total_datasets: 0,
                    });
                })
            );

            await getDatasets();

            // Characterization: Default sorting and pagination
            expect(capturedUrl).toBeDefined();
            const url = new URL(capturedUrl!);
            expect(url.searchParams.get('sort_by')).toBe('modified');
            expect(url.searchParams.get('order')).toBe('desc');
            expect(url.searchParams.get('page')).toBe('1');
            expect(url.searchParams.get('page_size')).toBe('25');
            expect(url.searchParams.get('include_counts')).toBe('true');
        });

        it('should transform query parameters to snake_case', async () => {
            let capturedUrl: string | undefined;

            server.use(
                http.get('/api/datasets', ({ request }) => {
                    capturedUrl = request.url;
                    return HttpResponse.json({
                        datasets: [],
                        total_datasets: 0,
                    });
                })
            );

            await getDatasets({
                platformId: 'platform-1',
                createdFrom: '2024-01-01',
                createdTo: '2024-12-31',
                isDeleted: false,
                sortBy: 'title',
                pageSize: 10,
            });

            const url = new URL(capturedUrl!);
            expect(url.searchParams.get('platform_id')).toBe('platform-1');
            expect(url.searchParams.get('created_from')).toBe('2024-01-01');
            expect(url.searchParams.get('created_to')).toBe('2024-12-31');
            expect(url.searchParams.get('is_deleted')).toBe('false');
            expect(url.searchParams.get('sort_by')).toBe('title');
            expect(url.searchParams.get('page_size')).toBe('10');
        });
    });

    describe('getPlatforms', () => {
        it('should transform platform response correctly', async () => {
            server.use(
                http.get('/api/platforms', () => {
                    return HttpResponse.json({
                        platforms: [
                            {
                                id: 'platform-1',
                                name: 'Test Platform',
                                slug: 'test-platform',
                                type: 'datagouv',
                                url: 'https://test.com',
                                created_at: '2024-01-01T00:00:00Z',
                                last_sync: '2024-01-10T00:00:00Z',
                                last_sync_status: 'success',
                                datasets_count: 100,
                            },
                        ],
                        total_platforms: 1,
                    });
                })
            );

            const result = await getPlatforms();

            // Characterization: created_at → created
            expect(result[0]).toMatchObject({
                id: 'platform-1',
                name: 'Test Platform',
                slug: 'test-platform',
                type: 'datagouv',
                url: 'https://test.com',
                created: '2024-01-01T00:00:00Z',
                lastSync: '2024-01-10T00:00:00Z',
                lastSyncStatus: 'success',
                datasetsCount: 100,
            });
        });
    });

    describe('getPublishers', () => {
        it('should return array of publishers', async () => {
            server.use(
                http.get('/api/publishers', () => {
                    return HttpResponse.json({
                        items: ['Publisher 1', 'Publisher 2', 'Publisher 3'],
                    });
                })
            );

            const result = await getPublishers();

            // Characterization: Direct array return
            expect(result).toEqual(['Publisher 1', 'Publisher 2', 'Publisher 3']);
        });

        it('should apply default limit parameter', async () => {
            let capturedUrl: string | undefined;

            server.use(
                http.get('/api/publishers', ({ request }) => {
                    capturedUrl = request.url;
                    return HttpResponse.json({ items: [] });
                })
            );

            await getPublishers();

            // Characterization: Default limit is 50
            const url = new URL(capturedUrl!);
            expect(url.searchParams.get('limit')).toBe('50');
        });
    });

    describe('Error Handling', () => {
        it('should throw on HTTP 404', async () => {
            server.use(
                http.get('/api/datasets', () => {
                    return HttpResponse.json(
                        { error: 'Not found' },
                        { status: 404 }
                    );
                })
            );

            await expect(getDatasets()).rejects.toThrow('HTTP 404');
        });

        it('should throw on HTTP 500', async () => {
            server.use(
                http.get('/api/datasets', () => {
                    return HttpResponse.json(
                        { error: 'Internal server error' },
                        { status: 500 }
                    );
                })
            );

            await expect(getDatasets()).rejects.toThrow('HTTP 500');
        });

        it('should include error payload in thrown error', async () => {
            server.use(
                http.get('/api/datasets', () => {
                    return HttpResponse.json(
                        { error: 'Validation failed', details: 'Invalid parameter' },
                        { status: 400 }
                    );
                })
            );

            try {
                await getDatasets();
                expect.fail('Should have thrown');
            } catch (error: any) {
                expect(error.status).toBe(400);
                expect(error.payload).toEqual({
                    error: 'Validation failed',
                    details: 'Invalid parameter',
                });
            }
        });
    });
});
