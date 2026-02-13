import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getDatasetDetail } from "../api/datasets";
import type { DatasetDetail } from "../types/datasets";
import { Badge } from "@codegouvfr/react-dsfr/Badge";
import { Alert } from "@codegouvfr/react-dsfr/Alert";

import { Breadcrumb } from "@codegouvfr/react-dsfr/Breadcrumb";

/**
 * Page dédiée au rendu du rapport d'audit qualité pour impression.
 * Optimisée pour le format A4 via @media print.
 */
export function AuditReportPage() {
  const { id } = useParams<{ id: string }>();
  const [dataset, setDataset] = useState<DatasetDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      getDatasetDetail(id)
        .then(setDataset)
        .catch((e: Error) => setError(e.message))
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading)
    return (
      <div className="fr-container fr-py-10w">Chargement du rapport...</div>
    );

  if (error || !dataset)
    return (
      <div className="fr-container fr-py-10w">
        <Alert
          severity="error"
          title="Erreur"
          description={error || "Jeu de données non trouvé"}
        />
      </div>
    );

  const results = dataset.quality?.evaluation_results;
  const score = results?.overall_score ?? 0;

  return (
    <div
      className="fr-container fr-py-2w print-optimized"
      style={{ maxWidth: "850px", margin: "0 auto" }}
    >
      <div className="no-print">
        <Breadcrumb
          segments={[
            { label: "Catalogue", linkProps: { href: "/datasets" } },
            {
              label: dataset.title ?? dataset.slug,
              linkProps: { href: `/datasets/${dataset.id}` },
            },
          ]}
          currentPageLabel="Rapport d'audit"
        />
      </div>

      {/* Styles d'impression ultra-compacts pour tenir sur 2 pages */}
      <style>{`
        @page {
          size: A4;
          margin: 15mm;
        }
        @media print {
          .fr-header, .fr-footer, .fr-btn, .no-print, .fr-breadcrumb { display: none !important; }
          body {
            background-color: white !important;
            font-size: 9pt !important;
            line-height: 1.2 !important;
          }
          .print-optimized {
            width: 100% !important;
            max-width: none !important;
            margin: 0 !important;
            padding: 0 !important;
          }
          h1, .fr-h1 { font-size: 18pt !important; margin-bottom: 0.2cm !important; }
          h4, .fr-h4 { font-size: 12pt !important; margin-top: 0.5cm !important; margin-bottom: 0.2cm !important; border-bottom: 1px solid #eee; padding-bottom: 2px; }
          h5, .fr-h5 { font-size: 10pt !important; margin-bottom: 0.1cm !important; margin-top: 0.3cm !important; }
          .fr-callout { padding: 0.5rem !important; margin-bottom: 0.5rem !important; break-inside: avoid; }
          .fr-callout__title { font-size: 10pt !important; }
          .fr-card { break-inside: avoid; border: 1px solid #ddd !important; padding: 0.75rem !important; }
          .criterion-block { break-inside: avoid; border: 1px solid #eee !important; padding: 0.75rem !important; margin-bottom: 0.25rem !important; }
          .fr-badge { font-size: 7pt !important; height: auto !important; line-height: 1 !important; padding: 2px 4px !important; }
          ul, li { font-size: 8pt !important; margin-bottom: 2px !important; }
          p { margin-bottom: 0.25rem !important; }
          .fr-mb-2w { margin-bottom: 0.5rem !important; }
          .fr-alert { padding: 0.5rem 1rem 0.5rem 3rem !important; margin-bottom: 0.5rem !important; }
          .fr-alert__title { font-size: 10pt !important; margin-bottom: 0 !important; }
          .fr-alert__description { font-size: 8pt !important; }
          .fr-grid-row--gutters { margin: -0.25rem !important; }
          .fr-grid-row--gutters > [class*="fr-col-"] { padding: 0.25rem !important; }
        }
        .criterion-block { border: 1px solid #e5e5e5; border-radius: 4px; padding: 1rem; margin-bottom: 1rem; }
        @media screen {
          .fr-callout { background-color: var(--background-alt-blue-france); }
        }
      `}</style>

      <div className="fr-grid-row fr-grid-row--middle fr-mb-2w fr-mt-2w">
        <div className="fr-col">
          <h1
            id="report-main-title"
            className="fr-h1 fr-mb-1w"
          >
            {dataset.title ?? dataset.slug}
          </h1>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <Badge noIcon>{dataset.slug}</Badge>
            <Badge
              noIcon
              severity="info"
            >
              Audit Qualité
            </Badge>
          </div>
        </div>
      </div>

      <div className="fr-grid-row fr-grid-row--gutters fr-mb-2w">
        <div className="fr-col-12 fr-col-md-6">
          <h4 className="fr-h4 fr-mb-1w">Score Global</h4>
          <Alert
            severity={
              score >= 70 ? "success" : score >= 50 ? "info" : "warning"
            }
            title={
              score >= 85
                ? "Qualité Excellente"
                : score >= 70
                  ? "Bonne Qualité"
                  : score >= 50
                    ? "Satisfaisante"
                    : "À améliorer"
            }
            description={`Score: ${Math.round(score)}/100`}
          />
        </div>
        <div className="fr-col-12 fr-col-md-6">
          <h4 className="fr-h4 fr-mb-1w">Statistiques</h4>
          <div className="fr-grid-row fr-grid-row--gutters">
            <div className="fr-col-6">
              <div
                className="fr-card fr-p-2w"
                style={{
                  textAlign: "center",
                  backgroundColor: "var(--background-alt-grey)",
                  boxShadow: "none",
                  border: "1px solid var(--border-default-grey)",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "center",
                  height: "100%",
                }}
              >
                <p
                  className="fr-text--bold fr-mb-0"
                  style={{
                    fontSize: "1.5rem",
                    color: "var(--text-title-blue-france)",
                    lineHeight: "1.2",
                  }}
                >
                  {dataset.currentSnapshot?.downloadsCount?.toLocaleString() ??
                    0}
                </p>
                <p
                  className="fr-text--xs fr-mb-0"
                  style={{ opacity: 0.8 }}
                >
                  Téléchargements
                </p>
              </div>
            </div>
            <div className="fr-col-6">
              <div
                className="fr-card fr-p-2w"
                style={{
                  textAlign: "center",
                  backgroundColor: "var(--background-alt-grey)",
                  boxShadow: "none",
                  border: "1px solid var(--border-default-grey)",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "center",
                  height: "100%",
                }}
              >
                <p
                  className="fr-text--bold fr-mb-0"
                  style={{
                    fontSize: "1.5rem",
                    color: "var(--text-title-blue-france)",
                    lineHeight: "1.2",
                  }}
                >
                  {dataset.currentSnapshot?.apiCallsCount?.toLocaleString() ??
                    0}
                </p>
                <p
                  className="fr-text--xs fr-mb-0"
                  style={{ opacity: 0.8 }}
                >
                  Appels API
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <section className="fr-mb-2w">
        <h4 className="fr-h4 fr-mb-1w">Analyse par critères</h4>
        {["administrative", "descriptive", "geotemporal"].map((cat) => {
          const criteria = Object.entries(
            results?.criteria_scores || {}
          ).filter(([_, s]: any) => s.category === cat);
          return (
            criteria.length > 0 && (
              <div
                key={cat}
                className="fr-mb-2w"
              >
                <h5 className="fr-h5 fr-mb-1w">
                  {cat === "administrative"
                    ? "Administration"
                    : cat === "descriptive"
                      ? "Description"
                      : "Géo-temporel"}
                </h5>
                <div className="fr-grid-row fr-grid-row--gutters">
                  {criteria.map(([key, s]: any) => (
                    <div
                      key={key}
                      className="fr-col-6"
                    >
                      <div className="criterion-block">
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                          }}
                          className="fr-mb-0"
                        >
                          <span className="fr-text--bold fr-text">
                            {s.criterion}
                          </span>
                          <Badge
                            noIcon
                            severity={
                              s.score >= 70
                                ? "success"
                                : s.score >= 50
                                  ? "info"
                                  : "warning"
                            }
                          >
                            {Math.round(s.score)}
                          </Badge>
                        </div>
                        {s.issues?.length > 0 && (
                          <ul className="fr-text--sm fr-mb-0 fr-mt-1w">
                            {s.issues
                              .slice(0, 2)
                              .map((i: string, idx: number) => (
                                <li key={idx}>{i}</li>
                              ))}
                          </ul>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          );
        })}
      </section>

      {results?.suggestions?.length > 0 && (
        <section className="fr-mb-2w">
          <h4 className="fr-h4 fr-mb-1w">Suggestions clés</h4>
          <div className="fr-grid-row fr-grid-row--gutters">
            {results.suggestions.slice(0, 6).map((s: any, i: number) => (
              <div
                key={i}
                className="fr-col-6"
              >
                <div
                  className="fr-card fr-p-1w"
                  style={{
                    borderLeft: "3px solid var(--border-default-blue-france)",
                    boxShadow: "none",
                    backgroundColor: "white",
                    border: "1px solid #eee",
                  }}
                >
                  <h5
                    className="fr-text--bold fr-text fr-mb-0"
                    style={{ color: "var(--text-title-blue-france)" }}
                  >
                    {s.field}
                  </h5>
                  <p className="fr-text fr-mb-0">
                    <strong>Value:</strong> {s.suggested_value}
                  </p>
                  <p
                    className="fr-text--xs fr-mb-0"
                    style={{ fontStyle: "italic" }}
                  >
                    {s.reason}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="no-print fr-mt-4w fr-grid-row fr-grid-row--right">
        <button
          className="fr-btn fr-btn--secondary"
          onClick={() => window.print()}
        >
          Imprimer le rapport
        </button>
      </div>
    </div>
  );
}
