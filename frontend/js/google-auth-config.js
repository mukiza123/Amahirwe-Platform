/**
 * "Continue with Google" is off until this has a real Client ID.
 *
 * To get one:
 *   1. https://console.cloud.google.com/ -> create/select a project.
 *   2. APIs & Services > OAuth consent screen -> User type "External",
 *      fill in app name + your email, add yourself as a test user
 *      (keeps the app in "Testing" mode, which skips Google's review).
 *   3. APIs & Services > Credentials > Create Credentials > OAuth
 *      client ID -> Application type "Web application".
 *   4. Under "Authorized JavaScript origins" add every URL this site is
 *      served from, e.g. http://127.0.0.1:5500 and http://localhost:5500
 *      for local dev, plus your real domain once deployed. No redirect
 *      URI is needed — this uses Google's popup/token flow, not a
 *      server-side redirect.
 *   5. Copy the Client ID (ends in .apps.googleusercontent.com) and
 *      paste it below.
 *   6. Set the same value as GOOGLE_CLIENT_ID in backend/.env — the
 *      backend independently verifies every token against it.
 */
export const GOOGLE_CLIENT_ID = "514591731261-oc7kb2i54ogujvmoi7e2hlh2opuac0mc.apps.googleusercontent.com";
