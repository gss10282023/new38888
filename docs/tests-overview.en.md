# Test Suite Overview (English)

This document explains the BIOTech Futures Hub test infrastructure in depth, detailing folder layout, individual test responsibilities, and execution workflows. It spans the Django REST backend, the Vue 3 frontend, and cross-layer integration scenarios so that contributors can confidently extend the quality baseline.

## 1. At a Glance
- **Root directory:** `tests/`
- **Coverage areas:**
  - `tests/backend/` – Django/DRF API and domain logic coverage
  - `tests/api/` – Cross-service authentication & admin workflow flows
  - `tests/integration/` – End-to-end collaboration and visibility checks
  - `tests/frontend/` – Pinia stores, Vue components, router guards, and utilities (unit + integration)
- **New frontend dev dependencies:** `vitest`, `@vue/test-utils`, `@testing-library/vue`, `@testing-library/jest-dom`, `msw`, etc. (tracked in `frontend/package.json`)
- **Backend dependencies:** no change – continue using `backend/requirements.txt`

## 2. Directory Layout

```
tests/
├── backend/                # Django/DRF tests: authentication, users, groups, resources, events, announcements, chat, core services
│   ├── base.py             # Shared helpers (user/group factories, auth setup)
│   └── test_*.py           # Feature-specific suites
├── api/                    # Cross-service contract tests (magic-link login, admin workflows)
├── integration/            # End-to-end flows (team collaboration, content access matrix)
└── frontend/               # Frontend tests
    ├── mocks/              # MSW handlers
    ├── unit/               # Pinia store / component / utility specs
    ├── integration/        # Router guard and multi-module specs
    └── vitest.setup.js     # Vitest bootstrap (jsdom, MSW, IntersectionObserver mock, etc.)
```

## 3. Test Inventory

### 3.1 Backend (`tests/backend/`)
| File | Focus |
| --- | --- |
| `base.py` | `AuthenticatedAPITestCase` with shortcuts for creating users (all roles), groups, milestones, tasks, plus forced authentication helpers. |
| `test_authentication.py` | Magic-link/OTP issuance, refresh token edge cases, cache invalidation, outbound email assertions. |
| `test_users_api.py` | `/users/me/` read/update, admin user list filters/pagination/export, status transitions, guardrails against self/superuser deletion. |
| `test_groups_api.py` | Role-based group visibility, “my groups”, detailed payload, task lifecycle (add/update), milestone CRUD, admin-only group creation/deletion, permission coverage. |
| `test_resources_api.py` | Role filtering, admin-protected uploads (storage mocked), cover updates, deletion. |
| `test_events_api.py` | Listing with filters, admin creation, attendee registration/duplicate handling, cover uploads. |
| `test_announcements_api.py` | Audience filtering, admin-only create/delete. |
| `test_chat_api.py` | Message pagination, parameter validation, membership enforcement, attachment payload checks. |
| `test_core_endpoints.py` | Health check (happy path + simulated DB/Redis failure), authenticated uploads, missing-file validation. |

### 3.2 Cross-Service API (`tests/api/`)
| File | Focus |
| --- | --- |
| `test_auth_flow.py` | Full magic-link login flow through profile update under a bearer session. |
| `test_admin_workflow.py` | Admin creates a group, queries dashboard stats, filters user list, updates student status – end-to-end console workflow. |

### 3.3 End-to-End Integration (`tests/integration/`)
| File | Focus |
| --- | --- |
| `test_group_collaboration_flow.py` | Admin group creation → student detail view → milestone/task creation → completion tracking. |
| `test_content_access_flow.py` | Verifies student vs. mentor visibility across resources, announcements, and events. |

### 3.4 Frontend Unit & Integration (`tests/frontend/`)
| File | Focus |
| --- | --- |
| `vitest.setup.js` | Boots jsdom, MSW, junction mocks (IntersectionObserver, `scrollTo`), and global assertions. |
| `mocks/server.js` | Default authentication MSW handlers; individual specs can extend via `server.use`. |
| `unit/AnimatedContent.spec.ts` | Ensures initial transform/opacity setup, animation trigger, and replays when props change. |
| `unit/authStore.spec.ts` | Magic link request, OTP verification, refresh retry behaviour, localStorage persistence. |
| `unit/groupsStore.spec.ts` | Group caching, detail hydration, milestone/task mutations, completion toggling. |
| `unit/adminStore.spec.ts` | Admin stats fetch, user list filters/pagination, filter option caching. |
| `unit/safeJson.spec.ts` | Graceful JSON parsing, non-JSON tolerance, 204 handling. |
| `integration/routerGuard.spec.ts` | Navigation guard assertions: anonymous redirect, authenticated login bypass. |

## 4. Environment Setup

### 4.1 Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
> `backend/manage.py` now prepends the repository root to `sys.path`, so Django detects the shared `tests` package automatically.

### 4.2 Frontend
```bash
cd frontend
npm install
```
Vitest scripts:
- `npm run test` – one-off run with coverage written to `tests/frontend/coverage`
- `npm run test:watch` – watch mode for local development

## 5. Suggested Execution Order
1. **Run everything with one command**
   ```bash
   chmod +x tests/run-all-tests.sh   # grant execute permission once
   ./tests/run-all-tests.sh
   ```
   > Executes backend (unit/API), cross-service flows, and frontend Vitest in order; if a step fails it still runs the remaining suites and surfaces the failure in the final exit code.

2. **Backend unit/API tests**
   ```bash
   cd backend
   python manage.py test tests.backend
   ```
3. **Cross-service/API flows**
   ```bash
   python manage.py test tests.api tests.integration
   ```
4. **Frontend unit/integration**
   ```bash
   cd ../frontend
   npm run test
   ```

## 6. Coverage Highlights
- **Authentication hardening:** Magic link, OTP, refresh tokens, cache hygiene.
- **Admin console:** Filters, pagination, CSV export, guardrails (self/superuser protection).
- **Collaboration workflows:** Group/milestone/task lifecycle, role permissions.
- **Content distribution:** Role-specific resource/event/announcement visibility, upload pipelines.
- **Realtime chat:** Pagination, attachment validation, access control.
- **Platform health:** DB/Redis diagnostics, upload endpoint validation.
- **Frontend state:** Session hydration, caching strategies, filter option memoisation, graceful error handling.
- **Frontend interaction:** Animation wrappers, router guards, utility robustness.

## 7. Troubleshooting
- **Database/cache errors:** Use SQLite + `LocMemCache`, mirroring the behaviour validated in `test_core_endpoints.py`.
- **MSW misses requests:** Tests assume `http://127.0.0.1:8000/api`; if `.env` overrides this, update handlers via `server.use`.
- **Vitest module resolution issues:** Execute from `frontend/` after installing dependencies. If paths change, adjust the `test.setupFiles` entry in `vite.config.js`.

## 8. Future Enhancements
- Add Cypress or Playwright browser E2E coverage for real UI/file upload scenarios.
- Split CI stages: backend (`manage.py test`) and frontend (`npm run test`) with coverage uploads.
- Build load/performance scripts for chat and resource uploads to stress-test concurrency.

---

The current suite safeguards core business flows, permission boundaries, and frontend-backend contracts. Expand the suite by adding new scenarios or helper utilities within the existing folders to keep the quality bar high.

---

**中文版:** 详见 `docs/tests-overview.md`。
