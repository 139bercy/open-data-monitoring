/**
 * DatasetTable Component Tests (Simplifié)
 *
 * Tests basiques pour démarrer - À étendre progressivement
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { DatasetTable } from "../../components/DatasetTable";
import { mockDatasets } from "../mockData";

describe("DatasetTable - Basic Tests", () => {
  describe("Rendering", () => {
    it("should render table element", () => {
      render(
        <DatasetTable
          items={mockDatasets}
          total={mockDatasets.length}
          page={1}
          pageSize={10}
        />
      );

      const table = screen.getByRole("table");
      expect(table).toBeInTheDocument();
    });

    it("should display dataset titles", () => {
      render(
        <DatasetTable
          items={mockDatasets}
          total={mockDatasets.length}
          page={1}
          pageSize={10}
        />
      );

      mockDatasets
        .filter((d) => d.title)
        .forEach((dataset) => {
          expect(screen.getByText(dataset.title!)).toBeInTheDocument();
        });
    });

    it("should display platform names", () => {
      render(
        <DatasetTable
          items={mockDatasets}
          total={mockDatasets.length}
          page={1}
          pageSize={10}
        />
      );

      const dataGouv = screen.getAllByText("data.gouv.fr");
      expect(dataGouv.length).toBeGreaterThan(0);

      const dataEco = screen.getAllByText("data.economie.gouv.fr");
      expect(dataEco.length).toBeGreaterThan(0);
    });
  });

  describe("Data Formatting", () => {
    it("should format dates correctly", () => {
      render(
        <DatasetTable
          items={[mockDatasets[0]]}
          total={1}
          page={1}
          pageSize={10}
        />
      );

      const expectedDate = new Date(
        mockDatasets[0].created
      ).toLocaleDateString();
      expect(screen.getByText(expectedDate)).toBeInTheDocument();
    });

    it("should format numbers with separators", () => {
      render(
        <DatasetTable
          items={[mockDatasets[0]]}
          total={1}
          page={1}
          pageSize={10}
        />
      );

      // viewsCount: 1000 → "1 000" en locale fr-FR
      expect(screen.getByText("1 000")).toBeInTheDocument();
    });

    it("should display em-dash for null/undefined values", () => {
      const datasetWithNull = {
        ...mockDatasets[1],
        publisher: null,
      };

      render(
        <DatasetTable
          items={[datasetWithNull]}
          total={1}
          page={1}
          pageSize={10}
        />
      );

      const emDashes = screen.getAllByText("—");
      expect(emDashes.length).toBeGreaterThan(0);
    });
  });

  describe("Loading States", () => {
    it("should show skeleton when loading", () => {
      const { container } = render(
        <DatasetTable
          items={[]}
          total={0}
          page={1}
          pageSize={10}
          loading={true}
          skeletonRowCount={5}
        />
      );

      const skeletons = container.querySelectorAll(".fr-skeleton");
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it("should set aria-busy when loading", () => {
      const { container } = render(
        <DatasetTable
          items={mockDatasets}
          total={mockDatasets.length}
          page={1}
          pageSize={10}
          loading={true}
        />
      );

      const busyElement = container.querySelector('[aria-busy="true"]');
      expect(busyElement).toBeInTheDocument();
    });
  });

  describe("Empty States", () => {
    it("should show info alert when no items", () => {
      render(
        <DatasetTable
          items={[]}
          total={0}
          page={1}
          pageSize={10}
          loading={false}
        />
      );

      expect(screen.getByText(/Aucun jeu de données/i)).toBeInTheDocument();
    });
  });

  describe("Sort Indicators", () => {
    it("should show ascending indicator when sorted ascending", () => {
      render(
        <DatasetTable
          items={mockDatasets}
          total={mockDatasets.length}
          page={1}
          pageSize={10}
          sortBy="title"
          order="asc"
        />
      );

      const titleButton = screen.getByRole("button", {
        name: /Trier par titre/i,
      });
      expect(titleButton.textContent).toContain("▲");
    });

    it("should show descending indicator when sorted descending", () => {
      render(
        <DatasetTable
          items={mockDatasets}
          total={mockDatasets.length}
          page={1}
          pageSize={10}
          sortBy="modified"
          order="desc"
        />
      );

      const modifiedButton = screen.getByRole("button", {
        name: /Trier par modifié le/i,
      });
      expect(modifiedButton.textContent).toContain("▼");
    });
  });

  describe("Pagination", () => {
    it("should render pagination component", () => {
      render(
        <DatasetTable
          items={mockDatasets}
          total={50}
          page={1}
          pageSize={10}
        />
      );

      const pagination = screen.getByRole("navigation", {
        name: /pagination/i,
      });
      expect(pagination).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("should have accessible table structure", () => {
      render(
        <DatasetTable
          items={mockDatasets}
          total={mockDatasets.length}
          page={1}
          pageSize={10}
        />
      );

      const table = screen.getByRole("table");
      expect(table).toBeInTheDocument();

      const columnHeaders = screen.getAllByRole("columnheader");
      expect(columnHeaders.length).toBeGreaterThan(0);
    });
  });
});
