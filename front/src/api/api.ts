export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export type ApiClientOptions = {
    baseUrl?: string;
    defaultHeaders?: Record<string, string>;
};

export type RequestOptions = {
    method?: HttpMethod;
    query?: Record<string, unknown>;
    body?: unknown;
    signal?: AbortSignal;
    headers?: Record<string, string>;
};

function toQueryString(query?: Record<string, unknown>): string {
    if (!query) return "";
    const params = new URLSearchParams();
    Object.entries(query).forEach(([key, value]) => {
        if (value === undefined || value === null || value === "") return;
        params.set(key, String(value));
    });
    const qs = params.toString();
    return qs ? `?${qs}` : "";
}

class ApiClient {
    private readonly baseUrl: string;
    private readonly defaultHeaders: Record<string, string>;

    constructor(options?: ApiClientOptions) {
        this.baseUrl = options?.baseUrl ?? "/api";
        this.defaultHeaders = {
            Accept: "application/json",
            ...(options?.defaultHeaders ?? {})
        };
    }

    async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
        const { method = "GET", query, body, signal, headers } = options;
        const url = `${this.baseUrl}${path}${toQueryString(query)}`;

        const init: RequestInit = {
            method,
            headers: {
                ...this.defaultHeaders,
                ...(body ? { "Content-Type": "application/json" } : {}),
                ...(headers ?? {})
            },
            signal
        };

        if (body !== undefined) {
            init.body = typeof body === "string" ? body : JSON.stringify(body);
        }

        const res = await fetch(url, init);
        const contentType = res.headers.get("content-type") ?? "";
        const parseJson = async () => (contentType.includes("application/json") ? await res.json() : (await res.text() as unknown));

        if (!res.ok) {
            const payload = await parseJson().catch(() => undefined);
            const err = new Error(`HTTP ${res.status} ${res.statusText}`);
            (err as any).status = res.status;
            (err as any).payload = payload;
            throw err;
        }

        return (await parseJson()) as T;
    }

    get<T>(path: string, query?: Record<string, unknown>, init?: Omit<RequestOptions, "method" | "query">) {
        return this.request<T>(path, { ...init, method: "GET", query });
    }

    post<T>(path: string, body?: unknown, init?: Omit<RequestOptions, "method" | "body">) {
        return this.request<T>(path, { ...init, method: "POST", body });
    }

    put<T>(path: string, body?: unknown, init?: Omit<RequestOptions, "method" | "body">) {
        return this.request<T>(path, { ...init, method: "PUT", body });
    }

    patch<T>(path: string, body?: unknown, init?: Omit<RequestOptions, "method" | "body">) {
        return this.request<T>(path, { ...init, method: "PATCH", body });
    }

    delete<T>(path: string, init?: Omit<RequestOptions, "method">) {
        return this.request<T>(path, { ...init, method: "DELETE" });
    }
}

// Always use relative "/api" so Browser -> (Vite dev proxy ->) Express proxy -> FastAPI.
// With PROXY_PORT set, Vite will forward /api to http://localhost:PROXY_PORT (see vite.config.ts).
export const api = new ApiClient({ baseUrl: "/api" });
export default api;
