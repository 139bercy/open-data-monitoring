/**
 * Utility to manage feature flags via URL parameters, localStorage, and environment variables (via API).
 */

let globalFeatures: Record<string, boolean> = {};

/**
 * Loads global feature flags from the backend.
 * This should be called at application startup.
 */
export const loadGlobalFeatures = async (apiClient: any): Promise<void> => {
  try {
    globalFeatures = await apiClient.get("/common/features");
  } catch (e) {
    console.error("Failed to load global features", e);
  }
};

export const isFeatureEnabled = (featureName: string): boolean => {
  if (typeof window === "undefined") return false;

  const globalStatus = globalFeatures[featureName];

  // 1. Master Switch: OFF
  if (globalStatus === "off") {
    return false;
  }

  // 2. Master Switch: ON
  if (globalStatus === "on") {
    return true;
  }

  // 3. Canary mode (beta)
  const params = new URLSearchParams(window.location.search);

  // Check URL for explicit enablement (e.g., ?enable=proconnect)
  if (params.get("enable") === featureName) {
    localStorage.setItem(`ff_${featureName}`, "true");
    return true;
  }

  // Check URL for explicit disablement (e.g., ?disable=proconnect)
  if (params.get("disable") === featureName) {
    localStorage.removeItem(`ff_${featureName}`);
    return false;
  }

  // Fallback to localStorage if in beta mode
  return (
    globalStatus === "beta" &&
    localStorage.getItem(`ff_${featureName}`) === "true"
  );
};
