/**
 * MSW Setup for API Tests
 * Centralized configuration for Mock Service Worker
 */

import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";

// Create server instance with permissive configuration
export const server = setupServer();

/**
 * Setup MSW for tests
 * Call this in describe blocks that need API mocking
 */
export const setupMSW = () => {
  beforeAll(() =>
    server.listen({
      onUnhandledRequest: "warn", // Warn instead of error to avoid test failures
    })
  );
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());
};

// Re-export for convenience
export { http, HttpResponse };
