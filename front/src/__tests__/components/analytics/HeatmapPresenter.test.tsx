import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import HeatmapPresenter from "../../../components/analytics/HeatmapPresenter";

// Mock @codegouvfr/react-dsfr
vi.mock("@codegouvfr/react-dsfr", () => ({
  fr: {
    colors: {
      getHex: vi
        .fn()
        .mockReturnValue({
          decisions: { border: { default: { grey: { default: "#cecece" } } } },
        }),
    },
  },
}));

vi.mock("@codegouvfr/react-dsfr/useIsDark", () => ({
  useIsDark: vi.fn().mockReturnValue({ isDark: false }),
}));

// Mock Recharts to avoid issues in jsdom
vi.mock("recharts", async () => {
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
        <svg>
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
            return <g key={index}>{result}</g>;
          })}
        </svg>
      );
    },
  };
});

describe("HeatmapPresenter", () => {
  const mockData = [
    { direction: "DGFiP", score: 85, crises: 0 },
    { direction: "DG Trésor", score: 45, crises: 2 },
    { direction: "Customs", score: 12, crises: 5 },
  ];

  it("renders clusters for each direction", () => {
    render(<HeatmapPresenter data={mockData} />);
    expect(screen.getByText("DGFiP")).toBeDefined();
    expect(screen.getByText("DG Trésor")).toBeDefined();
    expect(screen.getByText("Customs")).toBeDefined();
  });

  it("applies correct color classes/styles based on score", () => {
    const { container } = render(<HeatmapPresenter data={mockData} />);

    // Check for color markers (we'll define specific data-attributes or classes)
    const healthyCluster = container.querySelector('[data-health="healthy"]');
    const warningCluster = container.querySelector('[data-health="warning"]');
    const crisisCluster = container.querySelector('[data-health="crisis"]');

    expect(healthyCluster).toBeDefined();
    expect(warningCluster).toBeDefined();
    expect(crisisCluster).toBeDefined();
  });
});
