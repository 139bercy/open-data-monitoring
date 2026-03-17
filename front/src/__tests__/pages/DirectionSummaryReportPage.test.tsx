import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, it, expect, vi } from "vitest";
import { DirectionSummaryReportPage } from "../../pages/DirectionSummaryReportPage";
import api from "../../api/api";

// Mock the API
vi.mock("../../api/api", () => {
  const mockApi = { get: vi.fn() };
  return { api: mockApi, default: mockApi };
});

describe("DirectionSummaryReportPage", () => {
  it("renders loading state initially", () => {
    (api.get as any).mockReturnValue(new Promise(() => {})); // Never resolves to stay in loading

    render(
      <MemoryRouter initialEntries={["/reports/direction-summary/Finance"]}>
        <Routes>
          <Route
            path="/reports/direction-summary/:direction"
            element={<DirectionSummaryReportPage />}
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/Chargement/i)).toBeInTheDocument();
  });

  it("renders report data for the direction", async () => {
    (api.get as any).mockResolvedValue({
      stats: {
        direction: "Finance",
        score: 85,
        score_quality: 90,
        score_freshness: 80,
        score_engagement: 87,
        crises: 2,
        count: 100,
      },
      crises: [
        {
          id: "1",
          title: "Dataset 1",
          health_score: 40,
          health_quality_score: 30,
          health_freshness_score: 50,
          health_engagement_score: 40,
        },
      ],
    });

    render(
      <MemoryRouter initialEntries={["/reports/direction-summary/Finance"]}>
        <Routes>
          <Route
            path="/reports/direction-summary/:direction"
            element={<DirectionSummaryReportPage />}
          />
        </Routes>
      </MemoryRouter>
    );

    // Wait for the report to be rendered
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
        /Rapport Flash : Finance/i
      );
    });

    // Should display the MBI score
    expect(screen.getByText(/Index de Vitalité/i)).toBeInTheDocument();
    expect(screen.getByText(/85%/i)).toBeInTheDocument();
  });
});
