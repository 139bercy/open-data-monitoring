import { DatasetSummary } from "../types/datasets";

/**
 * Interface pour les colonnes de l'export CSV
 */
interface ExportColumn {
  header: string;
  key: keyof DatasetSummary | string;
  transform?: (value: any, item: DatasetSummary) => string;
}

/**
 * Configuration des colonnes pour l'export "données élargies"
 */
const EXPORT_COLUMNS: ExportColumn[] = [
  { header: "ID", key: "id" },
  { header: "Slug", key: "slug" },
  { header: "Titre", key: "title" },
  { header: "Producteur", key: "publisher" },
  { header: "Plateforme", key: "platformName" },
  { header: "Type Plateforme", key: "platformType" },
  {
    header: "Créé le",
    key: "created",
    transform: (v) => (v ? new Date(v).toISOString() : ""),
  },
  {
    header: "Modifié le",
    key: "modified",
    transform: (v) => (v ? new Date(v).toISOString() : ""),
  },
  { header: "Vues", key: "viewsCount" },
  { header: "Appels API", key: "apiCallsCount" },
  { header: "Téléchargements", key: "downloadsCount" },
  { header: "Réutilisations", key: "reusesCount" },
  { header: "Abonnés", key: "followersCount" },
  { header: "Popularité", key: "popularityScore" },
  { header: "Nombre de versions", key: "versionsCount" },
  {
    header: "Santé Global (%)",
    key: "healthScore",
    transform: (v) => (v != null ? Math.round(v).toString() : ""),
  },
  {
    header: "Santé Qualité (%)",
    key: "healthQualityScore",
    transform: (v) => (v != null ? Math.round(v).toString() : ""),
  },
  {
    header: "Santé Fraîcheur (%)",
    key: "healthFreshnessScore",
    transform: (v) => (v != null ? Math.round(v).toString() : ""),
  },
  {
    header: "Santé Engagement (%)",
    key: "healthEngagementScore",
    transform: (v) => (v != null ? Math.round(v).toString() : ""),
  },
  { header: "Publié", key: "published", transform: (v) => (v ? "Oui" : "Non") },
  {
    header: "Restreint",
    key: "restricted",
    transform: (v) => (v ? "Oui" : "Non"),
  },
  {
    header: "Supprimé",
    key: "isDeleted",
    transform: (v) => (v ? "Oui" : "Non"),
  },
  {
    header: "Date suppression",
    key: "deletedAt",
    transform: (v) => (v ? new Date(v).toISOString() : ""),
  },
  { header: "Statut Synchro", key: "lastSyncStatus" },
  { header: "URL Source", key: "page" },
];

/**
 * Échappe une valeur pour le format CSV
 */
function escapeCsvValue(value: any): string {
  if (value === null || value === undefined) return "";
  const str = String(value);
  if (str.includes(",") || str.includes('"') || str.includes("\n")) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

/**
 * Génère et déclenche le téléchargement d'un fichier CSV à partir d'une liste de jeux de données.
 * Mode stateless : ne dépend d'aucun état React, prend les données brutes en entrée.
 */
export function exportDatasetsToCsv(
  datasets: DatasetSummary[],
  filename: string = "export-datasets.csv"
): void {
  if (!datasets || datasets.length === 0) return;

  // 1. Génération de l'en-tête
  const headers = EXPORT_COLUMNS.map((col) => escapeCsvValue(col.header)).join(
    ","
  );

  // 2. Génération des lignes
  const rows = datasets.map((item) => {
    return EXPORT_COLUMNS.map((col) => {
      let value = (item as any)[col.key];
      if (col.transform) {
        value = col.transform(value, item);
      }
      return escapeCsvValue(value);
    }).join(",");
  });

  // 3. Assemblage du CSV (avec BOM pour Excel)
  const csvContent = "\uFEFF" + [headers, ...rows].join("\n");

  // 4. Déclenchement du téléchargement
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);

  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
