/**
 * Amahirwe: shared site behaviour for mobile nav, language switching,
 * and the offline indicator banner. Loaded on every page.
 */

const SUPPORTED_LANGS = ["rw", "en", "fr"];
const DEFAULT_LANG = "rw";
const LANG_STORAGE_KEY = "amahirwe_lang";

let translations = {};

function getStoredLang() {
  const stored = localStorage.getItem(LANG_STORAGE_KEY);
  return SUPPORTED_LANGS.includes(stored) ? stored : DEFAULT_LANG;
}

async function loadTranslations(lang) {
  try {
    const response = await fetch(`/locales/${lang}.json`);
    if (!response.ok) throw new Error("Failed to load locale file");
    translations = await response.json();
  } catch (err) {
    console.error("Could not load translations for", lang, err);
    translations = {};
  }
}

function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    const value = translations[key];
    if (value) el.textContent = value;
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    const value = translations[key];
    if (value) el.setAttribute("placeholder", value);
  });

  document.querySelectorAll(".lang-switch button").forEach((btn) => {
    btn.setAttribute("aria-pressed", String(btn.dataset.lang === getStoredLang()));
  });

  // Lets pages with JS-built text (e.g. a dashboard's "Muraho, <name>!"
  // heading) know a language switch happened, since that text has no
  // data-i18n attribute for applyTranslations() to update on its own.
  window.dispatchEvent(new CustomEvent("amahirwe:translationsapplied"));
}

async function setLanguage(lang) {
  if (!SUPPORTED_LANGS.includes(lang)) return;
  localStorage.setItem(LANG_STORAGE_KEY, lang);
  document.documentElement.setAttribute("lang", lang);
  await loadTranslations(lang);
  applyTranslations();
}

function initLanguageSwitcher() {
  document.querySelectorAll(".lang-switch button").forEach((btn) => {
    btn.addEventListener("click", () => setLanguage(btn.dataset.lang));
  });
}

function initMobileNav() {
  const toggle = document.querySelector(".navbar__toggle");
  const nav = document.querySelector(".navbar");
  if (!toggle || !nav) return;

  toggle.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("navbar--open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
}

function initOfflineBanner() {
  const banner = document.querySelector(".offline-banner");
  if (!banner) return;

  const update = () => {
    banner.classList.toggle("is-visible", !navigator.onLine);
  };

  window.addEventListener("online", update);
  window.addEventListener("offline", update);
  update();
}

document.addEventListener("DOMContentLoaded", async () => {
  document.documentElement.setAttribute("lang", getStoredLang());
  await loadTranslations(getStoredLang());
  applyTranslations();
  initLanguageSwitcher();
  initMobileNav();
  initOfflineBanner();

  import("./offline.js").then(({ registerServiceWorker }) => registerServiceWorker());
  import("./custom-select.js").then(({ initCustomSelects }) => initCustomSelects());
});

export { setLanguage, loadTranslations, applyTranslations };
