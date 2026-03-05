import { Navigate, useLocation } from "react-router-dom";
import authService from "../api/auth";

interface ProtectedRouteProps {
  children: JSX.Element;
}

export function ProtectedRoute({ children }: ProtectedRouteProps): JSX.Element {
  const location = useLocation();

  if (!authService.isAuthenticated()) {
    // Redirect to login page but save the current location to come back after login
    return (
      <Navigate
        to="/login"
        state={{ from: location }}
        replace
      />
    );
  }

  return children;
}

export default ProtectedRoute;
