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
import { AuditReportPage } from "./pages/AuditReportPage";
import { LoginPage } from "./pages/LoginPage";
import { RadarHealthPage } from "./pages/RadarHealthPage";
import { Home } from "./pages/Home";
import { ProtectedRoute } from "./components/ProtectedRoute";
import authService from "./api/auth";
import api from "./api/api";
import { loadGlobalFeatures } from "./utils/featureFlags";
// ...existing code...

startReactDsfr({ defaultColorScheme: "system" });

import { useEffect } from "react";

function App(): JSX.Element {
  const { isDark, setIsDark } = useIsDark();

  useEffect(() => {
    loadGlobalFeatures(api);
  }, []);

  // Handle token in URL hash (from OIDC callback)
  useEffect(() => {
    const hash = window.location.hash;
    if (hash && hash.includes("access_token=")) {
      const token = hash.split("access_token=")[1]?.split("&")[0];
      if (token) {
        localStorage.setItem("odm_token", token);
        // Clear hash and redirect to clean URL
        window.history.replaceState(null, "", window.location.pathname);
        window.location.reload(); // Reload to refresh auth state in all components
      }
    }
  }, []);

  return (
    <>
      <Header
        brandTop={<span>Bercy Hub</span>}
        serviceTitle="Open Data Monitoring"
        homeLinkProps={{ href: "/", title: "Accueil - Open Data Monitoring" }}
        quickAccessItems={
          [
            <Button
              priority="tertiary no outline"
              size="small"
              onClick={() => setIsDark(!isDark)}
              key="theme-toggle"
            >
              {isDark ? "Thème clair" : "Thème sombre"}
            </Button>,
            authService.isAuthenticated() && (
              <Button
                priority="tertiary no outline"
                size="small"
                onClick={() => authService.logout()}
                key="logout"
                iconId="fr-icon-logout-box-r-line"
              >
                Déconnexion
              </Button>
            ),
          ].filter(Boolean) as any
        }
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
          path="/login"
          element={<LoginPage />}
        />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />
        <Route
          path="/datasets"
          element={
            <ProtectedRoute>
              <DatasetListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/datasets/:id"
          element={
            <ProtectedRoute>
              <DatasetListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/platforms"
          element={
            <ProtectedRoute>
              <PlatformListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/reports/audit/:id"
          element={
            <ProtectedRoute>
              <AuditReportPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/radar"
          element={
            <ProtectedRoute>
              <RadarHealthPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="*"
          element={
            <Navigate
              to="/"
              replace
            />
          }
        />
      </Routes>

      <Footer
        accessibility="fully compliant"
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
