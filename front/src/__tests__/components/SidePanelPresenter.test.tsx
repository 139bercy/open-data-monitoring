import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SidePanelPresenter } from "../../components/analytics/SidePanelPresenter";
import { mockDatasets } from "../mockData";

describe("SidePanelPresenter", () => {
  const mockOnClose = vi.fn();
  const mockOnDatasetClick = vi.fn();

  it("should render the direction title", () => {
    render(
      <SidePanelPresenter
        isOpen={true}
        direction="Direction 1"
        datasets={[]}
        onClose={mockOnClose}
        onDatasetClick={mockOnDatasetClick}
      />
    );
    expect(screen.getByText("Direction 1")).toBeInTheDocument();
  });

  it("should render the list of datasets", () => {
    const datasets = mockDatasets.slice(0, 2);
    render(
      <SidePanelPresenter
        isOpen={true}
        direction="Direction 1"
        datasets={datasets}
        onClose={mockOnClose}
        onDatasetClick={mockOnDatasetClick}
      />
    );
    expect(screen.getByText(datasets[0].title!)).toBeInTheDocument();
    expect(screen.getByText(datasets[1].title!)).toBeInTheDocument();
  });

  it("should call onClose when close button is clicked", () => {
    render(
      <SidePanelPresenter
        isOpen={true}
        direction="Direction 1"
        datasets={[]}
        onClose={mockOnClose}
        onDatasetClick={mockOnDatasetClick}
      />
    );
    const closeButton = screen.getByRole("button", { name: /fermer/i });
    fireEvent.click(closeButton);
    expect(mockOnClose).toHaveBeenCalled();
  });

  it("should call onDatasetClick when a dataset is clicked", () => {
    const datasets = mockDatasets.slice(0, 1);
    render(
      <SidePanelPresenter
        isOpen={true}
        direction="Direction 1"
        datasets={datasets}
        onClose={mockOnClose}
        onDatasetClick={mockOnDatasetClick}
      />
    );
    const datasetRow = screen.getByText(datasets[0].title!);
    fireEvent.click(datasetRow);
    expect(mockOnDatasetClick).toHaveBeenCalledWith(datasets[0].id);
  });
});
