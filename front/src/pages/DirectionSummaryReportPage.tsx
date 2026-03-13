import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Badge } from "@codegouvfr/react-dsfr/Badge";
import { Table } from "@codegouvfr/react-dsfr/Table";
import { Notice } from "@codegouvfr/react-dsfr/Notice";
import api from "../api/api";

interface DirectionStats {
  direction: string;
  score: number;
  score_quality: number;
  score_freshness: number;
  score_engagement: number;
  crises: number;
  count: number;
}

interface DatasetCrisis {
  id: string;
  title: string;
  health_score: number;
  health_quality_score: number;
  health_freshness_score: number;
  health_engagement_score: number;
  page?: string;
}

export const DirectionSummaryReportPage: React.FC = () => {
  const { direction } = useParams<{ direction: string }>();
  const [stats, setStats] = useState<DirectionStats | null>(null);
  const [crises, setCrises] = useState<DatasetCrisis[]>([]);
  const [loading, setLoading] = useState(true);

  const isUnknown = direction === "Inconnu";
  const displayTitle = isUnknown ? "Producteur non identifié" : direction;

  useEffect(() => {
    const fetchReportData = async () => {
      try {
        const response = (await api.get(
          `/analytics/direction-health/${encodeURIComponent(direction || "")}`
        )) as { stats: any; crises: any[] };
        setStats(response.stats);
        setCrises(response.crises);

        // Signal pour Playwright (au cas où il resterait configuré, mais ici c'est pour le front)
        // On attend un peu que le rendu React soit stable avant de proposer l'impression
        setTimeout(() => {
          const readyElement = document.createElement("div");
          readyElement.id = "report-ready";
          document.body.appendChild(readyElement);
        }, 500);
      } catch (error) {
        console.error("Error fetching report data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchReportData();
  }, [direction]);

  if (loading)
    return (
      <div
        id="report-loading"
        className="fr-p-5w"
      >
        Chargement du rapport...
      </div>
    );
  if (!stats)
    return (
      <div
        id="report-error"
        className="fr-p-5w"
      >
        Producteur non trouvé.
      </div>
    );

  return (
    <div
      className="fr-container fr-py-4w print-content"
      style={{ backgroundColor: "#fff", color: "#161616" }}
    >
      <div className="fr-grid-row fr-grid-row--gutters fr-grid-row--middle fr-mb-2w">
        <div className="fr-col-8">
          <h1 className="fr-h2 fr-mb-1v">Rapport Flash : {displayTitle}</h1>
          <p className="fr-text--md fr-mb-0">
            Tableau de bord de santé Open Data (MBI)
          </p>
          <p
            className="fr-text--xs fr-mb-0"
            style={{ color: "var(--text-mention-grey)" }}
          >
            Périmètre : data.economie.gouv.fr (Ouverts & Publiés)
          </p>
          {isUnknown && (
            <p
              className="fr-text--xs fr-mb-0"
              style={{ fontStyle: "italic", opacity: 0.8 }}
            >
              Ce rapport regroupe tous les jeux de données sans producteur
              (publisher) renseigné.
            </p>
          )}
        </div>
        <div
          className="fr-col-4"
          style={{ textAlign: "right" }}
        >
          <div className="fr-text--xs fr-text--bold fr-mb-1v">
            Index de Vitalité (Global)
          </div>
          <Badge
            severity={
              stats.score >= 80
                ? "success"
                : stats.score >= 60
                  ? "info"
                  : stats.score >= 40
                    ? "warning"
                    : "error"
            }
            noIcon
            style={{ fontSize: "1.2rem", padding: "0.3rem 0.8rem" }}
          >
            {Math.round(stats.score)}%
          </Badge>
        </div>
      </div>

      <div className="fr-grid-row fr-grid-row--gutters fr-mb-3w">
        <div className="fr-col-4">
          <div
            className="fr-card fr-card--sm fr-card--no-border fr-p-1w"
            style={{ backgroundColor: "var(--background-alt-blue-france)" }}
          >
            <div className="fr-card__body">
              <h3 className="fr-card__title fr-text--sm fr-mb-1v">
                Qualité Technique
              </h3>
              <p className="fr-card__desc fr-h4 fr-mb-0">
                {Math.round(stats.score_quality)}%
              </p>
              <p
                className="fr-text--xs fr-mb-0"
                style={{ fontSize: "0.65rem" }}
              >
                DCAT, Slugs, Schémas
              </p>
            </div>
          </div>
        </div>
        <div className="fr-col-4">
          <div
            className="fr-card fr-card--sm fr-card--no-border fr-p-1w"
            style={{ backgroundColor: "var(--background-alt-blue-france)" }}
          >
            <div className="fr-card__body">
              <h3 className="fr-card__title fr-text--sm fr-mb-1v">Fraîcheur</h3>
              <p className="fr-card__desc fr-h4 fr-mb-0">
                {Math.round(stats.score_freshness)}%
              </p>
              <p
                className="fr-text--xs fr-mb-0"
                style={{ fontSize: "0.65rem" }}
              >
                Respect des fréquences
              </p>
            </div>
          </div>
        </div>
        <div className="fr-col-4">
          <div
            className="fr-card fr-card--sm fr-card--no-border fr-p-1w"
            style={{ backgroundColor: "var(--background-alt-blue-france)" }}
          >
            <div className="fr-card__body">
              <h3 className="fr-card__title fr-text--sm fr-mb-1v">
                Engagement
              </h3>
              <p className="fr-card__desc fr-h4 fr-mb-0">
                {Math.round(stats.score_engagement)}%
              </p>
              <p
                className="fr-text--xs fr-mb-0"
                style={{ fontSize: "0.65rem" }}
              >
                Usages API & DL
              </p>
            </div>
          </div>
        </div>
      </div>

      <section className="fr-mb-3w">
        <h2 className="fr-h4 fr-mb-1w">Synthèse du patrimoine</h2>
        <div className="fr-grid-row fr-grid-row--gutters">
          <div className="fr-col-6">
            <div className="fr-callout fr-p-1w fr-m-0">
              <h4 className="fr-callout__title fr-text--sm">Volume</h4>
              <p className="fr-text--md fr-mb-0">
                <strong>{stats.count}</strong> jeux de données.
              </p>
            </div>
          </div>
          <div className="fr-col-6">
            <div className="fr-callout fr-callout--pink-tuile fr-p-1w fr-m-0">
              <h4 className="fr-callout__title fr-text--sm">
                Points de Vigilance
              </h4>
              <p className="fr-text--md fr-mb-0">
                <strong>{stats.crises}</strong> datasets prioritaires.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="fr-mb-3w">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h2 className="fr-h4 fr-mb-1w">
            Top 10 Points de Vigilance (Priorités)
          </h2>
          <Badge
            severity="error"
            noIcon
            small
          >
            Score &lt; 50%
          </Badge>
        </div>
        {crises.length > 0 ? (
          <Table
            headers={["Dataset", "Score", "Axe Critique"]}
            data={crises.map((c) => {
              const scores = [
                { label: "Qualité", value: c.health_quality_score },
                { label: "Fraîcheur", value: c.health_freshness_score },
                { label: "Engagement", value: c.health_engagement_score },
              ].sort((a, b) => (a.value ?? 0) - (b.value ?? 0));

              return [
                <span className="fr-text--bold fr-text--xs">
                  {c.page ? (
                    <a
                      href={c.page}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        textDecoration: "underline",
                        color: "var(--text-action-high-blue-france)",
                      }}
                    >
                      {c.title || "Sans titre"}
                    </a>
                  ) : (
                    c.title || "Sans titre"
                  )}
                </span>,
                <Badge
                  severity="error"
                  noIcon
                  small
                  style={{ fontSize: "0.7rem" }}
                >
                  {Math.round(c.health_score)}%
                </Badge>,
                <span
                  className="fr-text--xs"
                  style={{
                    color: "var(--text-action-high-error)",
                    fontSize: "0.7rem",
                  }}
                >
                  {scores[0].label} ({Math.round(scores[0].value ?? 0)}%)
                </span>,
              ];
            })}
          />
        ) : (
          <p className="fr-text--xs">
            Aucun point de vigilance détecté (Périmètre :
            data.economie.gouv.fr).
          </p>
        )}
      </section>

      <Notice
        title="Concept de Points de Vigilance"
        description="Un point de vigilance est un jeu de données dont le score MBI est < 50%. Ce score indique une rupture de fraîcheur critique ou une absence de documentation technique. Analyse limitée aux jeux publiés et ouverts de la plateforme data.economie.gouv.fr."
        className="fr-mb-2w"
      />

      <div className="no-print fr-mt-4w fr-grid-row fr-grid-row--right">
        <button
          className="fr-btn fr-btn--primary"
          onClick={() => window.print()}
        >
          Imprimer / Sauvegarder en PDF
        </button>
      </div>

      <style>{`
                @page {
                    size: A4;
                    margin: 10mm 15mm;
                }
                @media print {
                    .fr-header, .fr-footer, .fr-btn, .no-print { display: none !important; }
                    body { background-color: white !important; font-size: 10pt !important; }
                    .fr-container { width: 100% !important; max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
                    .print-content { padding: 0 !important; }
                    h1, .fr-h1 { font-size: 18pt !important; margin-bottom: 0.5rem !important; }
                    h2, .fr-h2 { font-size: 14pt !important; margin-bottom: 0.5rem !important; }
                    h3, .fr-h3 { font-size: 12pt !important; margin-bottom: 0.25rem !important; }
                    h4, .fr-h4 { font-size: 10pt !important; margin-bottom: 0.25rem !important; }
                    .fr-card { border: 1px solid #eee !important; padding: 0.5rem !important; }
                    .fr-card__body { padding: 0 !important; }
                    .fr-callout { padding: 0.75rem !important; margin: 0 !important; }
                    .fr-table { margin-bottom: 0.5rem !important; }
                    .fr-table table { font-size: 9pt !important; }
                    .fr-notice { padding: 0.5rem !important; }
                    .fr-notice__title { font-size: 9pt !important; }
                    .fr-notice__desc { font-size: 8pt !important; }
                }
            `}</style>
    </div>
  );
};
