/* ===================================================================
   CPGE Flashcards -- API helper
   Shared by every page. Talks to the FastAPI backend at the same
   origin using relative URLs, and manages the JWT in localStorage.
   =================================================================== */

const TOKEN_KEY = "cpge_token";

/** Custom error carrying the HTTP status and parsed body, if any. */
class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function isLoggedIn() {
  return !!getToken();
}

/** Redirects to the login page if there is no token. Call at the top of every protected page. */
function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = "index.html";
    return false;
  }
  return true;
}

/** True if the current page is the login/register page (used to avoid redirect loops). */
function isAuthPage() {
  const p = window.location.pathname;
  return (
    p.endsWith("/index.html") ||
    p === "/" ||
    p.endsWith("/static/") ||
    p.endsWith("/static")
  );
}

/** Pulls a human-readable message out of a FastAPI error body. */
function formatErrorDetail(data) {
  if (!data || !data.detail) return "Something went wrong. Please try again.";
  const detail = data.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e) => (e && e.msg ? e.msg : JSON.stringify(e)))
      .join("; ");
  }
  return "Something went wrong. Please try again.";
}

/**
 * Calls the backend API.
 * @param {string} path - relative path, e.g. "/decks"
 * @param {object} options
 *   method: HTTP method, default GET
 *   body: object (JSON) or URLSearchParams (form)
 *   auth: whether to attach the Authorization header, default true
 *   isForm: send body as application/x-www-form-urlencoded instead of JSON
 */
async function apiFetch(path, options = {}) {
  const { method = "GET", body = null, auth = true, isForm = false } = options;

  const headers = {};
  if (body && !isForm) headers["Content-Type"] = "application/json";
  if (body && isForm) headers["Content-Type"] = "application/x-www-form-urlencoded";
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(path, {
      method,
      headers,
      body: body ? (isForm ? body.toString() : JSON.stringify(body)) : undefined,
    });
  } catch (networkErr) {
    throw new ApiError(
      "Can't reach the server. Check that the backend is running.",
      0,
      null
    );
  }

  if (response.status === 204) {
    return null;
  }

  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (e) {
      data = null;
    }
  }

  if (!response.ok) {
    if (response.status === 401 && auth) {
      clearToken();
      if (!isAuthPage()) {
        window.location.href = "index.html";
      }
    }
    throw new ApiError(formatErrorDetail(data), response.status, data);
  }

  return data;
}
