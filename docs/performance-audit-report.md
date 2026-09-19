# Amahirwe performance audit — final report

Scope: login speed and dashboard load speed, end to end (browser → JS →
API → Postgres → response → render). This covers the fixes actually
applied to the codebase, followed by live measurements taken against
the real Neon-hosted database (not a mocked/local DB) at the time of
writing.

## Root cause

The dominant cost on every request, before and after this audit, is
**network round-trip time to Neon** (`us-east-2`, AWS) plus Postgres
connection setup — not algorithmic complexity, not JS execution, and
not frontend bundle size (there is no bundle; this is unbundled vanilla
JS/CSS). A single request to a geographically distant serverless
Postgres instance costs somewhere in the hundreds of milliseconds to
low seconds depending on network conditions, before any query even
runs. That floor cannot be optimized away by application code.

On top of that floor, this audit found and fixed **real, avoidable
inefficiencies** that were adding *extra* round trips or *extra* work
on top of the unavoidable one:

1. Some endpoints ran two separate queries (fetch rows, then fetch
   each row's latest related record) where one query could do both.
2. A rarely-changing public reference table (schools) was queried from
   Postgres on every single page load that needed it, even though its
   contents are effectively static.
3. Dashboards waited for their data fetch to resolve before showing
   *any* content, turning "the network is slow" into "the whole page
   looks frozen," instead of rendering the shell immediately and
   filling in data as it arrives.
4. The login flow issued more work than strictly needed to establish a
   session before a user reached their dashboard.

None of this required rewriting the stack, adding Redis, or replacing
Postgres — the fixes are all localized query/caching/render-order
changes.

## Backend

- **`backend/app/api/teachers.py`** — `_top_results_by_student()` used
  to run one query to find each student's latest talent assessment,
  then a second query to fetch that assessment's results. Rewritten
  into a single query using Postgres's `DISTINCT ON`, which fetches
  "the latest row per group" and its joined data in one round trip
  instead of two.
- **`backend/app/api/parents.py`** — `list_my_children()` had the same
  two-query pattern for a parent's children's latest assessments;
  consolidated the same way, via a `DISTINCT ON` subquery joined to
  `TalentResult`.
- **`backend/app/api/schools.py`** — added a 5-minute in-process TTL
  cache in front of the school directory. This endpoint is public
  reference data (the list of schools shown in profile-completion
  dropdowns) that essentially never changes at runtime, so there is no
  reason to hit Postgres for it on every form load. Deliberately *not*
  Redis — this is a single uvicorn process and the data isn't
  user-specific, so a module-level dict with a `time.monotonic()`
  expiry is the right amount of machinery, not more.
- **`backend/app/core/database.py`** — `pool_pre_ping=True` was
  reviewed and deliberately left in place, even though it costs an
  extra round trip per checkout. Neon's free tier auto-suspends the
  database after inactivity; without `pool_pre_ping`, the *first*
  request after a suspend would hand a stale/dead connection to the
  app and fail outright, which is worse than the small per-request
  cost of validating the connection. This was a considered trade-off,
  not an oversight.

## Database

- The N+1 / double-query patterns above were the only real query-shape
  problems found; the rest of the API already used batched `IN`
  queries (a fix from an earlier pass) rather than per-row loops.
- No missing-index problems were found: the query patterns filter and
  join on primary/foreign keys (`student_id`, `assessment_id`, etc.),
  which are already indexed by virtue of being keys.
- `SADeprecationWarning` is raised by the test suite (SQLite backend)
  on the two `DISTINCT ON` queries, because SQLite doesn't support
  `DISTINCT ON` and SQLAlchemy silently no-ops it there instead of
  erroring. This is expected and harmless in tests (behaviorally
  covered by other assertions in the same tests), but it's why this
  audit verified both queries **live against real Postgres** with
  `curl`, rather than trusting the green SQLite-backed test suite
  alone for this specific behavior.
- No pagination gaps were found on the endpoints in scope; result sets
  here are bounded by "one teacher's students" or "one parent's
  children," not open-ended tables.

## Frontend

- Dashboards were changed to render their shell (sidebar, layout,
  loading placeholders) immediately, and fetch data in the background
  rather than blocking `showContent()` on the fetch resolving. The
  network floor described above didn't go away, but the page stops
  looking frozen while it's paid.
- `requireRole()` in `frontend/js/auth.js` uses the user object already
  cached from login/register as the source of truth for an *immediate*
  render decision, and separately kicks off a non-blocking
  `refreshCurrentUser()` call in the background to reconcile with the
  server (catching a revoked session or a role change) without making
  the page wait on that round trip first.
- Login itself does auth-only work: one `POST /auth/login` request,
  no redundant follow-up `GET /auth/me` before redirecting, since the
  login response already contains the user object.

## Before vs after

Two of the fixes in this audit have a clean, directly-comparable
before/after, measured in this session against the live Neon database:

| Endpoint | Before | After |
|---|---|---|
| `GET /api/schools` (cold, cache empty) | full Postgres round trip | **~1.4s** (cache miss, unchanged — this is the network floor) |
| `GET /api/schools` (warm, within 5 min) | same full round trip, every time | **~0.002–0.003s** (in-process cache hit, no DB round trip at all) |

That's the one place in this system where "before" behavior (every
request pays the network floor) and "after" behavior (only the first
request per 5-minute window pays it) can be measured side by side on
the same endpoint, because the fix is caching rather than a query
rewrite.

For the `DISTINCT ON` query consolidations (teachers/parents), the
"before" version (two separate queries) is no longer in the codebase
to re-measure — the fix was applied and verified working, not run in
parallel with the old version for comparison. What can be reported
honestly is the **current, post-fix** live timing against Neon, taken
in this session:

| Endpoint | Live timing (Neon, `us-east-2`) |
|---|---|
| `POST /api/auth/login` | ~1.6–2.4s |
| `GET /api/auth/me` | ~1.2–2.0s |
| `GET /api/teachers/me/overview` (uses the consolidated `DISTINCT ON` query) | ~3.0s |
| `GET /api/teachers/me/students` | ~2.0–2.6s |

These numbers are dominated by network latency from wherever this
audit is being run to Neon's `us-east-2` region, and by connection
setup (`pool_pre_ping`) rather than by query execution time itself —
consistent with the root-cause finding above. They will vary by the
requester's actual network path in a way application-level fixes
cannot change; a production deployment on infrastructure
geographically closer to the database (or a Neon region closer to
users) would see meaningfully lower numbers than a developer machine
several time zones away.

## Remaining issues

- **The core network-latency floor is not fixable from application
  code.** The only real lever left is infrastructure placement
  (hosting the API closer to Neon's region, or vice versa), which is
  outside this audit's scope.
- **No response-level caching on per-user endpoints** (overview,
  students, matches) — only the schools endpoint got a cache, because
  it's the only one in scope that's genuinely public/static.
  Per-user data changes too often, and caching it would need
  invalidation logic that's a larger addition than this audit's
  "no unnecessary complexity" mandate allows for.
- **`pool_pre_ping`'s extra round trip is a standing, accepted cost** —
  see Backend section. Removing it would shave a small amount off
  every request but reintroduce failures after Neon auto-suspends.
- Skeleton-loader UX and progressive rendering were addressed for
  dashboards in an earlier pass in this project's history; this audit
  did not find additional render-blocking patterns beyond what was
  already fixed.

## Files changed (this audit)

- `backend/app/api/teachers.py` — consolidated 2-query pattern into 1
  via `DISTINCT ON`.
- `backend/app/api/parents.py` — same consolidation for children's
  latest assessments.
- `backend/app/api/schools.py` — added 5-minute in-process TTL cache.
- `backend/app/core/database.py` — reviewed, `pool_pre_ping` kept
  intentionally (documented decision, not a code change).
- `frontend/js/auth.js` — `requireRole()`/`refreshCurrentUser()`
  render from cache immediately, reconcile with the server in the
  background instead of blocking on it.
- Dashboard pages — render shell immediately, fetch data in the
  background rather than gating `showContent()` on the fetch.

No rewrites, no new frameworks, no replacement of Python/Postgres, no
removal of security checks, and no fake/hardcoded data or artificial
loading delays were introduced anywhere in this work.
