/**
 * Amahirwe API client.
 * Every network call to the FastAPI backend goes through here, so there is
 * one place that knows about base URLs, auth headers, and error shape.
 */

// Same-origin in production (frontend and API share a domain behind Vercel);
// override for local development where the API runs on its own port.
const API_BASE_URL = (() => {
  const { hostname, port } = window.location;
  const isLocalStatic = hostname === "127.0.0.1" || hostname === "localhost";
  if (isLocalStatic && port !== "8000") {
    return "http://127.0.0.1:8000/api";
  }
  return "/api";
})();

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

function getToken() {
  return localStorage.getItem("amahirwe_token");
}

async function request(path, { method = "GET", body, auth = true, headers = {} } = {}) {
  const finalHeaders = { ...headers };
  let payload = body;

  if (body !== undefined && !(body instanceof FormData)) {
    finalHeaders["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  if (auth) {
    const token = getToken();
    if (token) {
      finalHeaders["Authorization"] = `Bearer ${token}`;
    }
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: finalHeaders,
      body: payload,
    });
  } catch (networkError) {
    throw new ApiError("We couldn't reach the server. Check your connection.", 0, null);
  }

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await response.json().catch(() => null) : null;

  if (!response.ok) {
    const message = (data && (data.detail || data.message)) || "Something went wrong. Please try again.";
    throw new ApiError(typeof message === "string" ? message : "Something went wrong.", response.status, data);
  }

  return data;
}

const api = {
  get: (path, opts) => request(path, { ...opts, method: "GET" }),
  post: (path, body, opts) => request(path, { ...opts, method: "POST", body }),
  put: (path, body, opts) => request(path, { ...opts, method: "PUT", body }),
  patch: (path, body, opts) => request(path, { ...opts, method: "PATCH", body }),
  delete: (path, opts) => request(path, { ...opts, method: "DELETE" }),
};

export { api, ApiError, getToken };
