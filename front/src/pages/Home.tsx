import { Button } from "@codegouvfr/react-dsfr/Button";
import { Link } from "react-router-dom";

export function Home(): JSX.Element {
  return (
    <div className="fr-container fr-my-6w">
      <h1 className="fr-h1">Open Data Monitoring</h1>
      <p className="fr-text--lg">
        Suivez l'état des jeux de données et des plateformes.
      </p>

      <div className="fr-grid-row fr-grid-row--gutters fr-mt-4w">
        <div className="fr-col-12 fr-col-md-6">
          <Link
            to="/datasets"
            className="fr-btn"
          >
            Consulter les jeux de données
          </Link>
        </div>
        <div className="fr-col-12 fr-col-md-6">
          <Link
            to="/platforms"
            className="fr-btn"
          >
            Voir les plateformes
          </Link>
        </div>
      </div>
    </div>
  );
}
