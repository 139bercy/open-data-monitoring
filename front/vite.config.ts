/// <reference types="node" />
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// Vite configuration with API proxy resolved from .env (API_URL, API_PORT)
export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), "");
    const proxyPort = env.PROXY_PORT;
    const ensureHttpProtocol = (raw?: string) => (raw ? (/^https?:\/\//i.test(raw) ? raw : `http://${raw}`) : undefined);
    const apiUrl = ensureHttpProtocol(env.API_URL);
    const apiPort = env.API_PORT;
    const apiTarget = env.API_TARGET;
    const isFullTarget = !!(apiTarget && /^https?:\/\//i.test(apiTarget));
    const isPathTarget = !!(apiTarget && apiTarget.startsWith("/"));
    // If PROXY_PORT is set, route Vite dev proxy to the local Express proxy (Browser -> Vite -> Express -> FastAPI)
    // Otherwise, fallback to direct API_URL:API_PORT
    const target = proxyPort
        ? `http://localhost:${proxyPort}`
        : isFullTarget
            ? apiTarget!
            : `${(apiUrl ?? "").replace(/\/$/, "")}${apiPort ? `:${apiPort}` : ""}`;

    return {
        plugins: [react()],
        server: {
            proxy: {
                "/api": {
                    target,
                    changeOrigin: true,
                    secure: false,
                    rewrite: !proxyPort && isPathTarget ? (p) => p.replace(/^\/api/, apiTarget!) : undefined
                }
            }
        }
    };
});


