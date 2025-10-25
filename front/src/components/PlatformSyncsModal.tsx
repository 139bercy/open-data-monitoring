import { createModal } from "@codegouvfr/react-dsfr/Modal";
import type { PlatformRef, PlatformSync } from "../types/datasets";

export const platformSyncsModal = createModal({
  id: "platform-syncs-modal",
  isOpenedByDefault: false,
});

export function PlatformSyncsModal(props: {
  platform: PlatformRef | null;
}): JSX.Element {
  return (
    <platformSyncsModal.Component
      title={
        props.platform
          ? `Synchronisations - ${props.platform.name}`
          : "Synchronisations"
      }
      size="lg"
    >
      {props.platform ? (
        <div>
          <div className="fr-mb-3w">
            <p className="fr-text--lg fr-mb-1w">
              <strong>{props.platform.slug}</strong>
            </p>
            <p className="fr-text--sm fr-text--grey">
              {props.platform.syncs && props.platform.syncs.length > 0
                ? `${props.platform.syncs.length} synchronisation${props.platform.syncs.length > 1 ? "s" : ""}`
                : "Aucune synchronisation"}
            </p>
          </div>

          {props.platform.syncs && props.platform.syncs.length > 0 ? (
            <div className="fr-grid-row fr-grid-row--gutters">
              {props.platform.syncs.map((sync: PlatformSync) => (
                <div
                  key={sync.id}
                  className="fr-col-12"
                >
                  <div
                    className="fr-card fr-card--grey fr-p-2w"
                    style={{ marginBottom: "1rem" }}
                  >
                    <div className="fr-grid-row fr-grid-row--gutters">
                      <div className="fr-col-12 fr-col-md-8">
                        <div className="fr-mb-2w">
                          <p className="fr-text--xs fr-text--uppercase fr-m-0 fr-text--bold">
                            Date
                          </p>
                          <p className="fr-text--sm fr-m-0 fr-text--grey">
                            {new Date(sync.timestamp).toLocaleString("fr-FR", {
                              timeZone: "UTC",
                            })}
                          </p>
                        </div>
                        <div className="fr-mb-2w">
                          <p className="fr-text--xs fr-text--uppercase fr-m-0 fr-text--bold">
                            Statut
                          </p>

                          <p
                            className={`fr-text--sm fr-m-0 ${
                              sync.status === "success"
                                ? "fr-text--success"
                                : sync.status === "failed"
                                  ? "fr-text--error"
                                  : "fr-text--warning"
                            }`}
                          >
                            {sync.status === "success"
                              ? "✓ Succès"
                              : sync.status === "failed"
                                ? "✗ Échec"
                                : "⚠ Succès partiel"}
                          </p>
                        </div>
                      </div>

                      <div className="fr-col-12 fr-col-md-4">
                        <div className="fr-mb-2w">
                          <p className="fr-text--xs fr-text--uppercase fr-m-0 fr-text--bold">
                            Jeux de données
                          </p>
                          <p className="fr-text--lg fr-m-0 fr-text--bold">
                            {sync.datasets_count}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="fr-alert fr-alert--info fr-mb-2w">
              <p>Aucune synchronisation enregistrée pour cette plateforme.</p>
            </div>
          )}
        </div>
      ) : (
        <div className="fr-alert fr-alert--info">
          <p>Sélectionnez une plateforme pour voir ses synchronisations.</p>
        </div>
      )}
    </platformSyncsModal.Component>
  );
}
