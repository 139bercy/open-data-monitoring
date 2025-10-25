import { useEffect, useMemo, useState } from "react";
import { Alert } from "@codegouvfr/react-dsfr/Alert";
import { Button } from "@codegouvfr/react-dsfr/Button";
import type { PlatformRef } from "../types/datasets";
import { getPlatforms } from "../api/datasets";
import {platformSyncsModal, PlatformSyncsModal} from "../components/PlatformSyncsModal";

export function PlatformListPage(): JSX.Element {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [platforms, setPlatforms] = useState<PlatformRef[]>([]);

  const [modalPlatform, setModalPlatform] = useState<PlatformRef | null>(null);

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
    <>
      <div className="fr-container fr-my-6w">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h1 className="fr-h1">{title}</h1>
          <nav
            className="fr-breadcrumb"
            aria-label="fil d’Ariane"
          >
            <ol className="fr-breadcrumb__list">
              <li className="fr-breadcrumb__item">
                <a
                  className="fr-breadcrumb__link"
                  href="/"
                >
                  Accueil
                </a>
              </li>
              <li
                className="fr-breadcrumb__item"
                aria-current="page"
              >
                Plateformes
              </li>
            </ol>
          </nav>
        </div>

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
              <div className="fr-card__body fr-p-2w">
                <div className="fr-grid-row fr-grid-row--gutters">
                  <div className="fr-col-12">
                    <h5 className="fr-mb-1w">
                      {platform.name ?? platform.slug}
                    </h5>
                    <p className="fr-text--sm fr-text--grey fr-m-0">
                      {platform.type}
                    </p>
                  </div>

                  <div className="fr-col-12 fr-col-md-6">
                    <div className="fr-mb-2w">
                      <p className="fr-text--xs fr-text--uppercase fr-m-0 fr-text--bold">
                        Slug
                      </p>
                      <p className="fr-text--sm fr-m-0 fr-text--grey">
                        {platform.slug}
                      </p>
                    </div>
                    <div className="fr-mb-2w">
                      <p className="fr-text--xs fr-text--uppercase fr-m-0 fr-text--bold">
                        Créée
                      </p>
                      <p className="fr-text--sm fr-m-0 fr-text--grey">
                        {new Date(platform.created).toLocaleString("fr-FR", {
                          timeZone: "UTC",
                        }) ?? "—"}
                      </p>
                    </div>
                    <div className="fr-mb-2w">
                      <p className="fr-text--xs fr-text--uppercase fr-m-0 fr-text--bold">
                        Dernière synchronisation
                      </p>
                      <p className="fr-text--sm fr-m-0 fr-text--grey">
                        {platform.lastSync
                          ? new Date(platform.lastSync).toLocaleString(
                              "fr-FR",
                              { timeZone: "UTC" }
                            )
                          : "Jamais"}
                      </p>
                    </div>
                  </div>

                  <div className="fr-col-12 fr-col-md-6">
                    <div className="fr-mb-2w">
                      <p className="fr-text--xs fr-text--uppercase fr-m-0 fr-text--bold">
                        Clé API
                      </p>
                      <p className="fr-text--sm fr-m-0 fr-text--grey">
                        {platform.key ? "✓ Configurée" : "—"}
                      </p>
                    </div>
                    <div className="fr-mb-2w">
                      <p className="fr-text--xs fr-text--uppercase fr-m-0 fr-text--bold">
                        Jeux de données
                      </p>
                      <p className="fr-text--sm fr-m-0 fr-text--grey">
                        {platform.datasetsCount ? platform.datasetsCount : "—"}
                      </p>
                    </div>
                    <div className="fr-col-auto">
                      {platform.syncs?.length >= 1 && (
                          <Button
                              priority="secondary"
                              onClick={() => {
                                platformSyncsModal.open();
                                setModalPlatform(platform);
                              }}
                          >
                            Voir synchronisations
                          </Button>
                      )}
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
      <PlatformSyncsModal platform={modalPlatform} />
    </>
  );
}
