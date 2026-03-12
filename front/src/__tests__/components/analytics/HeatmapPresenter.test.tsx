import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import HeatmapPresenter from "../../../components/analytics/HeatmapPresenter";

// Mock @codegouvfr/react-dsfr/useIsDark
vi.mock("@codegouvfr/react-dsfr/useIsDark", () => ({
  useIsDark: vi.fn().mockReturnValue({ isDark: false }),
}));

// Mock Recharts to avoid issues in jsdom and allow inspection of props
vi.mock("recharts", async () => {
  const React = await import("react");
  const original = await vi.importActual("recharts");
  return {
    ...original,
    ResponsiveContainer: ({ children }: any) => (
      <div style={{ width: 800, height: 400 }}>{children}</div>
    ),
    Treemap: (props: any) => {
      const { data, content } = props;
      if (!data) return null;
      return (
        <svg data-testid="recharts-treemap">
          {data.map((item: any, index: number) => {
            const result =
              typeof content === "function"
                ? content({
                    ...item,
                    x: index * 100,
                    y: 0,
                    width: 100,
                    height: 100,
                  })
                : React.cloneElement(content, {
                    ...item,
                    x: index * 100,
                    y: 0,
                    width: 100,
                    height: 100,
                  });
            return (
              <g
                key={index}
                data-testid={`cluster-${item.direction}`}
              >
                {result}
              </g>
            );
          })}
        </svg>
      );
    },
    // Mock Tooltip content to be rendered immediately for testing if needed,
    // but usually we test the custom content logic instead.
  };
});

describe("HeatmapPresenter", () => {
  const mockData = [
    { direction: "DGFiP", score: 95, crises: 0, count: 100 },
    { direction: "INSEE", score: 75, crises: 1, count: 50 },
    { direction: "DG Trésor", score: 30, crises: 10, count: 200 },
    { direction: "Customs", score: 10, crises: 15, count: 10 },
  ];

  it("renders clusters for each direction with correct accessibility icons", () => {
    render(<HeatmapPresenter data={mockData} />);
    expect(screen.getByText(/🌟 DGFiP/)).toBeDefined();
    expect(screen.getByText(/🍃 INSEE/)).toBeDefined();
    expect(screen.getByText(/🚨 DG Trésor/)).toBeDefined();
    expect(screen.getByText(/🔥 Customs/)).toBeDefined();
  });

  it("applies continuous color scaling based on score", () => {
    const { getByTestId } = render(<HeatmapPresenter data={mockData} />);

    const dgipRect = getByTestId("cluster-DGFiP").querySelector("rect");
    const customsRect = getByTestId("cluster-Customs").querySelector("rect");

    const dgipFill = dgipRect?.getAttribute("fill");
    const customsFill = customsRect?.getAttribute("fill");

    // High score (95) should be green-ish (hue near 125)
    expect(dgipFill).toContain("hsl");
    // Low score (10) should be red-ish (hue near 0)
    expect(customsFill).toContain("hsl");
    expect(dgipFill).not.toBe(customsFill);
  });

  it("calculates health attributes for data testing", () => {
    const { getByTestId } = render(<HeatmapPresenter data={mockData} />);

    expect(getByTestId("cluster-DGFiP").firstChild).toHaveAttribute(
      "data-health",
      "excellent"
    );
    expect(getByTestId("cluster-Customs").firstChild).toHaveAttribute(
      "data-health",
      "critical"
    );
  });

  it("calls onClusterClick when a rect is clicked", () => {
    const handleClick = vi.fn();
    const { getByTestId } = render(
      <HeatmapPresenter
        data={mockData}
        onClusterClick={handleClick}
      />
    );

    const dgipCluster = getByTestId("cluster-DGFiP").firstChild;
    if (dgipCluster) fireEvent.click(dgipCluster);

    expect(handleClick).toHaveBeenCalledWith("DGFiP");
  });

  it("filters and labels correctly", () => {
    render(<HeatmapPresenter data={mockData} />);
    expect(screen.getByText(/Échelle Logarithmique/)).toBeDefined();
    expect(screen.getByText(/CRITIQUE/)).toBeDefined();
    expect(screen.getByText(/EXCELLENT/)).toBeDefined();
  });
});
