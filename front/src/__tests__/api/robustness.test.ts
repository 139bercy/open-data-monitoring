import { describe, it, expect, vi } from "vitest";
import { server, setupMSW, http, HttpResponse } from "./setup";
import { syncDatasetFromSource } from "../../api/datasets";

describe("API Client - Robustness Tests", () => {
  setupMSW();

  describe("syncDatasetFromSource", () => {
    const testUrl =
      "https://data.economie.gouv.fr/explore/dataset/test-sync/information/";

    it("should call the correct endpoint with encoded URL", async () => {
      let capturedUrl: string | undefined;

      server.use(
        http.post("/api/datasets/add", ({ request }) => {
          capturedUrl = request.url;
          return HttpResponse.json({
            status: "success",
            dataset_id: "test-sync",
          });
        })
      );

      await syncDatasetFromSource(testUrl);

      expect(capturedUrl).toContain("/api/datasets/add");
      const url = new URL(capturedUrl!);
      expect(url.searchParams.get("url")).toBe(testUrl);
    });

    it("should handle API 500 error when dataset sync fails in backend", async () => {
      server.use(
        http.post("/api/datasets/add", () => {
          return HttpResponse.json(
            { detail: "'NoneType' object is not subscriptable" },
            { status: 500 }
          );
        })
      );

      await expect(syncDatasetFromSource(testUrl)).rejects.toThrow("HTTP 500");
    });

    it("should handle malformed ODS URLs that might cause fetch failures", async () => {
      const malformedUrl =
        "https://data.economie.gouv.fr/explore/dataset/invalid-id/information/";

      server.use(
        http.post("/api/datasets/add", () => {
          return HttpResponse.json(
            { status: "error", message: "Dataset not found" },
            { status: 404 }
          );
        })
      );

      await expect(syncDatasetFromSource(malformedUrl)).rejects.toThrow(
        "HTTP 404"
      );
    });
  });
});
