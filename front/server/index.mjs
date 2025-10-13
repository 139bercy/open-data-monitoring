import express from "express";
import helmet from "helmet";
import morgan from "morgan";
import cors from "cors";
import { createProxyMiddleware } from "http-proxy-middleware";
import path from "node:path";
import { fileURLToPath } from "node:url";
// Load .env from project root (front/.env) even if started from server/
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontRoot = path.resolve(__dirname, "..");
const envPath = path.join(frontRoot, ".env");

const app = express();
const PORT = process.env.PROXY_PORT;

// Ensure a raw host like "localhost" gets an explicit http:// scheme
function ensureHttpProtocol(raw) {
    if (!raw) return undefined;
    return /^https?:\/\//i.test(raw) ? raw : `http://${raw}`;
}

const rawTarget = process.env.API_TARGET;
const rawApiUrl = ensureHttpProtocol(process.env.API_URL);
const apiPort = process.env.API_PORT;

let API_ORIGIN = rawApiUrl ? `${rawApiUrl.replace(/\/$/, "")}${apiPort ? `:${apiPort}` : ""}` : undefined;
let API_PATH_PREFIX = "";

if (rawTarget) {
    if (/^https?:\/\//i.test(rawTarget)) {
        API_ORIGIN = rawTarget.replace(/\/+$/, "");
        API_PATH_PREFIX = "";
    } else if (rawTarget.startsWith("/")) {
        API_PATH_PREFIX = rawTarget; // e.g., /api/v1
    }
}

if (!API_ORIGIN) {
    // eslint-disable-next-line no-console
    console.error("Missing API origin. Set API_URL (+ optional API_PORT) or API_TARGET as full URL.");
    process.exit(1);
}

app.disable("x-powered-by");
app.use(helmet());
app.use(morgan("tiny"));
app.use(cors({ origin: true, credentials: true }));

app.use(
    "/api",
    createProxyMiddleware({
        target: API_ORIGIN,
        changeOrigin: true,
        xfwd: true,
        secure: false,
        pathRewrite: API_PATH_PREFIX
            ? (path) => `${API_PATH_PREFIX.replace(/\/$/, "")}${path}`
            : undefined
    })
);

app.listen(PORT, () => {
    // eslint-disable-next-line no-console
    console.log(`Proxy listening on http://localhost:${PORT} -> ${API_ORIGIN}${API_PATH_PREFIX ? ` (rewrite ^/api -> ${API_PATH_PREFIX})` : ""}`);
});


