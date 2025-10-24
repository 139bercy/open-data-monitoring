import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { startReactDsfr } from "@codegouvfr/react-dsfr/spa";
import { Header } from "@codegouvfr/react-dsfr/Header";
import { Footer } from "@codegouvfr/react-dsfr/Footer";
import { useIsDark } from "@codegouvfr/react-dsfr/useIsDark";
import { Button } from "@codegouvfr/react-dsfr/Button";
import "@codegouvfr/react-dsfr/dsfr/dsfr.min.css";
import { DatasetListPage } from "./pages/DatasetListPage";
import { PlatformListPage } from "./pages/PlatformListPage";
// ...existing code...

startReactDsfr({ defaultColorScheme: "system" });

function App(): JSX.Element {
  const { isDark, setIsDark } = useIsDark();
  return (
    <>
      <Header
        brandTop={<span>Bercy Hub</span>}
        serviceTitle="Open Data Monitoring"
        homeLinkProps={{ href: "/", title: "Accueil - Open Data Monitoring" }}
        quickAccessItems={[
          <Button
            priority="tertiary no outline"
            size="small"
            onClick={() => setIsDark(!isDark)}
            key="theme-toggle"
          >
            {isDark ? "Thème clair" : "Thème sombre"}
          </Button>,
        ]}
      />
      {/* Global hover polish (kept subtle, DSFR-friendly) */}
      <style>{`
                .fr-table table tbody tr{transition:background-color .15s ease}
                .fr-table table tbody tr:hover{background-color:var(--background-alt-grey)}
                .fr-input:hover, .fr-select:hover, .fr-btn:hover{transition:transform .12s ease; transform:translateY(-1px)}
            `}</style>

      {/* Routes */}
      <Routes>
        <Route
          path="/datasets"
          element={<DatasetListPage />}
        />
        <Route
          path="/platforms"
          element={<PlatformListPage />}
        />
        <Route
          path="/"
          element={
            <Navigate
              to="/datasets"
              replace
            />
          }
        />
        <Route
          path="*"
          element={
            <Navigate
              to="/datasets"
              replace
            />
          }
        />
      </Routes>

      <Footer
        bottomItems={[
          <a
            className="fr-footer__bottom-link"
            href="#"
            key="mentions"
          >
            Mentions légales
          </a>,
        ]}
      />
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
);
