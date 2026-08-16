// Central fetch wrapper: always sends the session cookie, and handles 401
// in exactly one place (BR5) rather than repeating it per API call site.
//
// NFR Requirements chose CORS over a dev proxy (Q1=B) specifically so the
// frontend and backend can be different origins - which means requests
// need the backend's absolute URL, not a relative path (a relative path
// would just hit whatever's serving the frontend itself).

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

interface ApiOptions extends RequestInit {
  // AuthContext's initial "am I logged in" check on mount *expects* a 401
  // as a normal outcome - redirecting on that specific call would fire a
  // hard reload before React Router ever gets to render /login itself.
  // Every other call site wants the automatic redirect (BR5).
  skipAuthRedirect?: boolean;
}

export async function apiFetch(path: string, options: ApiOptions = {}): Promise<Response> {
  const { skipAuthRedirect, ...init } = options;
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  if (response.status === 401) {
    if (!skipAuthRedirect && window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
    throw new ApiError(401, "Not authenticated");
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body.detail ?? response.statusText);
  }

  return response;
}

export async function apiJson<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const response = await apiFetch(path, options);
  return response.json() as Promise<T>;
}
