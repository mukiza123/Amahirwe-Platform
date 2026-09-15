/**
 * Amahirwe: registration, login, logout, and session handling.
 * The token itself is only ever trusted by the backend; this file just
 * stores it and redirects; it never decides who is "allowed" to see a page.
 */

import { api, ApiError } from "./api.js";

const TOKEN_KEY = "amahirwe_token";
const USER_KEY = "amahirwe_user";

const DASHBOARD_BY_ROLE = {
  student: "student/dashboard.html",
  teacher: "teacher/dashboard.html",
  mentor: "mentor/dashboard.html",
  provider: "provider/dashboard.html",
  admin: "admin/dashboard.html",
  parent: "parent/dashboard.html",
};

function saveSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function getCurrentUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function isLoggedIn() {
  return Boolean(localStorage.getItem(TOKEN_KEY));
}

function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  window.location.href = pathToRoot() + "login.html";
}

/** Path prefix back to frontend/ root, based on current page depth. */
function pathToRoot() {
  const inRoleFolder = /\/frontend\/(student|teacher|mentor|provider|admin|parent)\//.test(window.location.pathname);
  return inRoleFolder ? "../" : "";
}

function dashboardUrlFor(role) {
  return pathToRoot() + (DASHBOARD_BY_ROLE[role] || "index.html");
}

/**
 * Guard for dashboard pages: redirects to login if there's no session,
 * and to that role's own dashboard if the logged-in user has a different
 * role. The real access control happens on the backend regardless.
 */
async function requireRole(expectedRole) {
  if (!isLoggedIn()) {
    window.location.href = pathToRoot() + "login.html";
    return null;
  }

  // Login already gave us the user object; if it matches the role this
  // page expects, use it immediately instead of spending a whole
  // network round trip re-asking the server who we are before the page
  // can even start rendering. refreshCurrentUser() still checks in the
  // background (without making the page wait) so a revoked session or
  // an actual role change still gets caught — this is a UX shortcut
  // only, the backend enforces the real access control on every data
  // call regardless of what this cache says.
  const cachedUser = getCurrentUser();
  if (cachedUser && cachedUser.role === expectedRole) {
    refreshCurrentUser(expectedRole);
    return cachedUser;
  }

  try {
    const user = await api.get("/auth/me");
    localStorage.setItem(USER_KEY, JSON.stringify(user));

    if (user.role !== expectedRole) {
      window.location.href = dashboardUrlFor(user.role);
      return null;
    }

    return user;
  } catch (err) {
    // Only a real "you're not authenticated" response should sign the
    // user out. A network hiccup or a slow/cold backend (status 0 or a
    // 5xx) is not proof the session is invalid, so let the caller's own
    // error handling show a retry-able message instead of discarding a
    // perfectly good token.
    if (err instanceof ApiError && err.status === 401) {
      logout();
      return null;
    }
    throw err;
  }
}

/** Fire-and-forget: reconciles the cached user with the server after
 * the page has already rendered from cache. Never blocks the caller. */
function refreshCurrentUser(expectedRole) {
  api
    .get("/auth/me")
    .then((user) => {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      if (user.role !== expectedRole) {
        window.location.href = dashboardUrlFor(user.role);
      }
    })
    .catch((err) => {
      if (err instanceof ApiError && err.status === 401) {
        logout();
      }
    });
}

function setFormError(form, message) {
  const el = form.querySelector("#form-error");
  if (el) {
    el.textContent = message;
    el.hidden = !message;
  }
}

function setFieldError(form, fieldName, message) {
  const el = form.querySelector(`#${fieldName}-error`);
  const input = form.querySelector(`#${fieldName}`);
  if (el) {
    el.textContent = message || "";
    el.hidden = !message;
  }
  if (input) {
    input.classList.toggle("has-error", Boolean(message));
  }
}

function clearErrors(form) {
  setFormError(form, "");
  form.querySelectorAll(".form-error[id]").forEach((el) => {
    el.textContent = "";
    el.hidden = true;
  });
  form.querySelectorAll(".has-error").forEach((el) => el.classList.remove("has-error"));
}

function setLoading(button, isLoading) {
  button.classList.toggle("btn-loading", isLoading);
  button.disabled = isLoading;
}

function initLoginForm() {
  const form = document.querySelector("#login-form");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearErrors(form);

    const email = form.email.value.trim();
    const password = form.password.value;
    const submitBtn = form.querySelector('button[type="submit"]');

    setLoading(submitBtn, true);
    try {
      const data = await api.post("/auth/login", { email, password }, { auth: false });
      saveSession(data.access_token, data.user);
      window.location.href = dashboardUrlFor(data.user.role);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setFormError(form, "Incorrect email or password.");
      } else {
        setFormError(form, err.message || "Something went wrong. Please try again.");
      }
    } finally {
      setLoading(submitBtn, false);
    }
  });
}

function initRegisterForm() {
  const form = document.querySelector("#register-form");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearErrors(form);

    const full_name = form.full_name.value.trim();
    const email = form.email.value.trim();
    const password = form.password.value;
    const role = form.role.value;
    const submitBtn = form.querySelector('button[type="submit"]');

    if (password.length < 8) {
      setFieldError(form, "password", "Password must be at least 8 characters.");
      return;
    }

    setLoading(submitBtn, true);
    try {
      const data = await api.post("/auth/register", { full_name, email, password, role }, { auth: false });
      saveSession(data.access_token, data.user);
      window.location.href = dashboardUrlFor(data.user.role);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setFieldError(form, "email", "An account with this email already exists.");
      } else {
        setFormError(form, err.message || "Something went wrong. Please try again.");
      }
    } finally {
      setLoading(submitBtn, false);
    }
  });
}

/** Wires up the "Change password" form on the settings page (present
 * for every role, same markup each time), including it here rather
 * than duplicating this in six settings.html files. */
function initPasswordForm() {
  const form = document.querySelector("#password-form");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearErrors(form);
    document.querySelector("#password-form-success")?.setAttribute("hidden", "");

    const current_password = form.current_password.value;
    const new_password = form.new_password.value;
    const confirm_password = form.confirm_password.value;
    const submitBtn = form.querySelector('button[type="submit"]');

    if (new_password.length < 8) {
      setFieldError(form, "new_password", "Password must be at least 8 characters.");
      return;
    }
    if (new_password !== confirm_password) {
      setFieldError(form, "confirm_password", "Passwords don't match.");
      return;
    }

    setLoading(submitBtn, true);
    try {
      await api.post("/auth/me/password", { current_password, new_password });
      form.reset();
      const success = document.querySelector("#password-form-success");
      if (success) success.hidden = false;
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setFieldError(form, "current_password", "Current password is incorrect.");
      } else {
        setFormError(form, err.message || "Something went wrong. Please try again.");
      }
    } finally {
      setLoading(submitBtn, false);
    }
  });
}

function initLogoutButtons() {
  document.querySelectorAll("[data-action='logout']").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      logout();
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initLoginForm();
  initRegisterForm();
  initPasswordForm();
  initLogoutButtons();
});

export {
  requireRole,
  getCurrentUser,
  isLoggedIn,
  logout,
  dashboardUrlFor,
  setFormError,
  setFieldError,
  clearErrors,
  setLoading,
};
