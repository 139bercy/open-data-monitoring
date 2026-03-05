import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Input } from "@codegouvfr/react-dsfr/Input";
import { Button } from "@codegouvfr/react-dsfr/Button";
import { Alert } from "@codegouvfr/react-dsfr/Alert";
import authService from "../api/auth";

export function LoginPage(): JSX.Element {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();

  // @ts-ignore - 'from' exists in state if redirected from ProtectedRoute
  const from = location.state?.from?.pathname || "/";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await authService.login(email, password);
      navigate(from, { replace: true });
    } catch (err: any) {
      console.error("Login error:", err);
      setError(
        err.payload?.detail || "Identifiants invalides ou erreur serveur."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fr-container fr-my-12w">
      <div className="fr-grid-row fr-grid-row--center">
        <div className="fr-col-12 fr-col-md-6 fr-col-lg-4">
          <div
            className="fr-card fr-p-4w"
            style={{ border: "1px solid var(--border-default-grey)" }}
          >
            <h1 className="fr-h2 fr-mb-4w">Connexion</h1>

            {error && (
              <Alert
                severity="error"
                title="Erreur d'authentification"
                description={error}
                className="fr-mb-3w"
              />
            )}

            <div className="fr-mt-4w">
              <Button
                priority="secondary"
                style={{ width: "100%", justifyContent: "center" }}
                onClick={() =>
                  (window.location.href = "/api/v1/auth/login/proconnect")
                }
                iconId="fr-icon-account-line"
              >
                S'identifier avec ProConnect
              </Button>
            </div>

            <div
              className="fr-mt-2w fr-mb-2w"
              style={{ textAlign: "center", position: "relative" }}
            >
              <hr
                style={{
                  border: "0",
                  borderTop: "1px solid var(--border-default-grey)",
                }}
              />
              <span
                style={{
                  position: "absolute",
                  top: "50%",
                  left: "50%",
                  transform: "translate(-50%, -50%)",
                  background: "white",
                  padding: "0 10px",
                  fontSize: "0.8rem",
                  color: "var(--text-mention-grey)",
                }}
              >
                ou
              </span>
            </div>

            <form onSubmit={handleSubmit}>
              <Input
                label="Email"
                nativeInputProps={{
                  type: "email",
                  value: email,
                  onChange: (e) => setEmail(e.target.value),
                  required: true,
                  autoComplete: "email",
                }}
              />
              <Input
                label="Mot de passe"
                nativeInputProps={{
                  type: "password",
                  value: password,
                  onChange: (e) => setPassword(e.target.value),
                  required: true,
                  autoComplete: "current-password",
                }}
              />

              <div className="fr-mt-4w">
                <Button
                  nativeButtonProps={{ type: "submit" }}
                  disabled={loading}
                  style={{ width: "100%", justifyContent: "center" }}
                >
                  {loading ? "Connexion..." : "Se connecter"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
