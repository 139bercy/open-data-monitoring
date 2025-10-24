import { useEffect, useMemo, useState } from "react";
import { Alert } from "@codegouvfr/react-dsfr/Alert";
import { Button } from "@codegouvfr/react-dsfr/Button";
import type { PlatformRef } from "../types/datasets";
import { getPlatforms } from "../api/datasets";

export function PlatformListPage(): JSX.Element {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [platforms, setPlatforms] = useState<PlatformRef[]>([]);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    getPlatforms()
      .then((data) => {
        if (!mounted) return;
        setPlatforms(data ?? []);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!mounted) return;
        setError(
          typeof err === "string"
            ? err
            : err instanceof Error
              ? err.message
              : "Erreur lors du chargement des plateformes"
        );
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const title = useMemo(() => "Plateformes", []);

  const platformNameById = useMemo(() => {
    const map = new Map<string, string>();
    platforms.forEach((p) => map.set(p.id, p.name ?? p.slug));
    return map;
  }, [platforms]);

  return (
    <div className="fr-container fr-my-6w">
      <h1 className="fr-h1">{title}</h1>

      <div>
        {loading && <p>Chargement...</p>}
        {!loading && platforms.length === 0 && (
          <p>Aucune plateforme disponible.</p>
        )}
        {platforms.map((platform) => (
          <div
            key={platform.id}
            className="fr-card fr-card--grey fr-my-2w"
          >
            <div className="fr-card__body">
              <div className="fr-grid-row fr-grid-row--gutters">
                {/* En-tête principal */}
                <div className="fr-col-12">
                  <h5 className="fr-mb-1w">{platform.name ?? platform.slug}</h5>
                  <p className="fr-text--sm fr-text--grey fr-m-0">{platform.type}</p>
                </div>

                <div className="fr-col-12 fr-col-md-6">
                  <div className="fr-mb-2w">
                    <p className="fr-text--xs fr-text--uppercase fr-m-0 fr-text--bold">
                      Slug
                    </p>
                    <p className="fr-text--sm fr-m-0 fr-text--grey">{platform.slug}</p>
                  </div>
                  <div className="fr-mb-2w">
                    <p className="fr-text--xs fr-text--uppercase fr-m-0 fr-text--bold">
                      Créée
                    </p>
                    <p className="fr-text--sm fr-m-0 fr-text--grey">
                      {platform.created ?? "—"}
                    </p>
                  </div>
                </div>

                {/* Colonne droite : Synchronisation et clé */}
                <div className="fr-col-12 fr-col-md-6">
                  <div className="fr-mb-2w">
                    <p className="fr-text--xs fr-text--uppercase fr-m-0 fr-text--bold">
                      Dernière sync
                    </p>
                    <p className="fr-text--sm fr-m-0 fr-text--grey">
                      {platform.lastSync ? platform.lastSync.split('T')[0] : "Jamais"}
                    </p>
                  </div>
                  <div className="fr-mb-2w">
                    <p className="fr-text--xs fr-text--uppercase fr-m-0 fr-text--bold">
                      Clé API
                    </p>
                    <p className="fr-text--sm fr-m-0 fr-text--grey">
                      {platform.key ? "✓ Configurée" : "—"}
                    </p>
                  </div>
                </div>

                {platform.url && (
                    <div className="fr-col-12 fr-mt-1w">
                      <a
                          href={platform.url}
                          target="_blank"
                          rel="noreferrer"
                          className="fr-link"
                      >
                        Accéder à la plateforme →
                      </a>
                    </div>
                )}
              </div>
            </div>

          </div>
        ))}
      </div>
      {error && (
        <Alert
          severity="error"
          title="Erreur"
          description={error}
          className="fr-mb-3w"
        />
      )}

      <div className="fr-mt-6w">
        <Button
          priority="tertiary no outline"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
        >
          Revenir en haut de page
        </Button>
      </div>
    </div>
  );
}
