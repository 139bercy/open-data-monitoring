import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, it, expect, vi } from "vitest";
import { DirectionSummaryReportPage } from "../../../pages/DirectionSummaryReportPage";
import { useDirectionHealth } from "../../../api/analytics";

// Mock the API hook
vi.mock("../../../api/analytics", () => ({ useDirectionHealth: vi.fn() }));

describe("DirectionSummaryReportPage", () => {
  it("renders loading state initially", () => {
    (useDirectionHealth as any).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
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

    expect(screen.getByText(/Chargement/i)).toBeInTheDocument();
  });

  it("renders report data for the direction", () => {
    (useDirectionHealth as any).mockReturnValue({
      data: [
        { direction: "Finance", score: 85, crises: 2, count: 100 },
        { direction: "RH", score: 70, crises: 5, count: 50 },
      ],
      isLoading: false,
      error: null,
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

    // Check title and indicator that the report is ready
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      /Bilan Santé Data : Finance/i
    );
    // Should display the MBI score
    expect(screen.getByText(/Score Global/i)).toBeInTheDocument();
    expect(screen.getByText(/85/i)).toBeInTheDocument();
  });
});
