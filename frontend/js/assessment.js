/**
 * Amahirwe: talent assessment flow (questions, progress, offline answers).
 * Implemented in Phase 3 (Student) and extended in Phase 4 (Offline).
 */

import { api, ApiError } from "./api.js";
import { queueAssessment } from "./offline.js";

const QUESTIONS_CACHE_KEY = "amahirwe_questions_cache";

/** Tries the network first so the question bank stays current, falling
 * back to whatever was cached from the last successful load. */
async function loadQuestions() {
  try {
    const questions = await api.get("/assessments/questions");
    localStorage.setItem(QUESTIONS_CACHE_KEY, JSON.stringify(questions));
    return questions;
  } catch (err) {
    const cached = localStorage.getItem(QUESTIONS_CACHE_KEY);
    if (cached) return JSON.parse(cached);
    throw err;
  }
}

/** Submits the assessment. If the network is unreachable, the answers
 * are queued locally instead of being lost, and the caller is told so
 * it can show "saved, will sync later" instead of an error. */
async function submitAssessment(payload) {
  try {
    const result = await api.post("/assessments", payload);
    return { queued: false, result };
  } catch (err) {
    const isNetworkError = err instanceof ApiError && err.status === 0;
    if (!isNetworkError) throw err;
    await queueAssessment(payload);
    return { queued: true, result: null };
  }
}

export { loadQuestions, submitAssessment };
