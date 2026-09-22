/**
 * Amahirwe: registration, login, logout, and session handling.
 * The token itself is only ever trusted by the backend; this file just
 * stores it and redirects; it never decides who is "allowed" to see a page.
 */

import { api, ApiError } from "./api.js";
import { GOOGLE_CLIENT_ID } from "./google-auth-config.js";

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

/** Path prefix back to frontend/ root, based on current page depth.
 *
 * Checks for a role-folder segment right after the leading slash (e.g.
 * "/student/dashboard.html"), NOT "/frontend/student/...". The browser
 * never actually sees "/frontend/" in the URL: on Vercel, vercel.json's
 * rewrite to "/frontend/$1" happens server-side, invisible to
 * window.location; and the local dev server (dev-server.py) is meant
 * to be run from inside frontend/, serving it as the web root the same
 * way. A "/frontend/" prefix check here previously never matched
 * either environment, so pathToRoot() always returned "" — meaning
 * every redirect issued from inside a role folder (logout,
 * dashboardUrlFor, verifyUrlFor, ...) resolved one level too shallow
 * and 404'd. */
function pathToRoot() {
  const inRoleFolder = /^\/(student|teacher|mentor|provider|admin|parent)\//.test(window.location.pathname);
  return inRoleFolder ? "../" : "";
}

function dashboardUrlFor(role) {
  return pathToRoot() + (DASHBOARD_BY_ROLE[role] || "index.html");
}

function verifyUrlFor() {
  return pathToRoot() + "verify.html";
}

/**
 * Guard for dashboard pages: redirects to login if there's no session,
 * to verify.html if the account hasn't confirmed its email yet, and to
 * that role's own dashboard if the logged-in user has a different
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
    if (!cachedUser.email_verified) {
      window.location.href = verifyUrlFor();
      return null;
    }
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
    if (!user.email_verified) {
      window.location.href = verifyUrlFor();
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
      } else if (!user.email_verified) {
        window.location.href = verifyUrlFor();
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
      window.location.href = data.user.email_verified ? dashboardUrlFor(data.user.role) : verifyUrlFor();
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
    if (form.agree_terms && !form.agree_terms.checked) {
      setFormError(form, "Please agree to the Terms of Service and Privacy Policy to continue.");
      return;
    }

    setLoading(submitBtn, true);
    try {
      const data = await api.post("/auth/register", { full_name, email, password, role }, { auth: false });
      saveSession(data.access_token, data.user);
      if (data.user.email_verified) {
        window.location.href = dashboardUrlFor(data.user.role);
        return;
      }
      // Stands in for the real email: there's no mail service
      // configured for this prototype, so verify.html reads the code
      // straight out of the register response instead of an inbox.
      // Session-scoped and read-once on purpose, not a persistent
      // credential store.
      if (data.dev_verification_code) {
        sessionStorage.setItem("amahirwe_dev_verification_code", data.dev_verification_code);
      }
      window.location.href = verifyUrlFor();
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

/** Show/hide toggle on a password field: [data-toggle-password] button
 * flips its target input between type="password" and type="text". */
function initPasswordToggles() {
  document.querySelectorAll("[data-toggle-password]").forEach((btn) => {
    const input = document.querySelector(btn.dataset.togglePassword);
    if (!input) return;
    btn.addEventListener("click", () => {
      const showing = input.type === "text";
      input.type = showing ? "password" : "text";
      btn.setAttribute("aria-label", showing ? "Show password" : "Hide password");
      btn.innerHTML = showing
        ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>'
        : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.94 10.94 0 0112 20c-7 0-11-8-11-8a21.3 21.3 0 015.06-6.06M9.9 4.24A10.94 10.94 0 0112 4c7 0 11 8 11 8a21.4 21.4 0 01-3.22 4.4M14.12 14.12a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
    });
  });
}

/** Facebook/Apple buttons are visual placeholders only — this app has
 * no real OAuth app registered with either of them. Clicking one says
 * so instead of doing nothing with no explanation. Google is excluded
 * here once it's configured (see initGoogleSignIn), since that one is
 * real. */
function initSocialAuthPlaceholders() {
  document.querySelectorAll("[data-social-auth]").forEach((btn) => {
    if (btn.dataset.socialAuth === "Google" && GOOGLE_CLIENT_ID) return;
    btn.addEventListener("click", () => {
      const note = document.querySelector("#auth-social-note");
      if (note) {
        note.textContent = `Sign-in with ${btn.dataset.socialAuth} isn't available in this prototype yet — use email above.`;
        note.hidden = false;
      }
    });
  });
}

/** Renders Google's real "Continue with Google" button into every
 * [data-google-signin] mount point and hides this page's placeholder
 * Google button, but only once a Client ID has actually been
 * configured (see google-auth-config.js) — otherwise the placeholder
 * stays exactly as it was, so nothing breaks before that setup step. */
function initGoogleSignIn() {
  const mounts = document.querySelectorAll("[data-google-signin]");
  if (!mounts.length || !GOOGLE_CLIENT_ID) return;

  if (!window.google?.accounts?.id) {
    // The GIS script tag loads async; it may not have finished yet.
    window.setTimeout(initGoogleSignIn, 300);
    return;
  }

  window.google.accounts.id.initialize({
    client_id: GOOGLE_CLIENT_ID,
    callback: handleGoogleCredential,
  });

  mounts.forEach((mount) => {
    mount.hidden = false;
    window.google.accounts.id.renderButton(mount, {
      type: "standard",
      theme: "outline",
      size: "large",
      shape: "pill",
      text: mount.dataset.googleSignin || "continue_with",
      width: Math.round(mount.getBoundingClientRect().width) || 320,
    });
    const placeholder = mount.parentElement?.querySelector('[data-social-auth="Google"]');
    if (placeholder) placeholder.hidden = true;
  });
}

async function handleGoogleCredential(response) {
  const note = document.querySelector("#auth-social-note");
  try {
    const data = await api.post("/auth/google", { id_token: response.credential }, { auth: false });
    if (data.needs_role) {
      // No account exists for this Google email yet — hold onto the
      // token (short-lived, re-verified fresh on the next call) and
      // let the role-picker page finish the sign-up.
      sessionStorage.setItem("amahirwe_google_id_token", response.credential);
      window.location.href = pathToRoot() + "google-role.html";
      return;
    }
    saveSession(data.access_token, data.user);
    window.location.href = data.user.email_verified ? dashboardUrlFor(data.user.role) : verifyUrlFor();
  } catch (err) {
    if (note) {
      note.textContent = err.message || "Google sign-in failed. Please try again.";
      note.hidden = false;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initLoginForm();
  initRegisterForm();
  initPasswordForm();
  initLogoutButtons();
  initPasswordToggles();
  initSocialAuthPlaceholders();
  initGoogleSignIn();
});

export {
  requireRole,
  getCurrentUser,
  saveSession,
  isLoggedIn,
  logout,
  dashboardUrlFor,
  verifyUrlFor,
  setFormError,
  setFieldError,
  clearErrors,
  setLoading,
};
