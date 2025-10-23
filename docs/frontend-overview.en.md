# BIOTech Futures Hub – Frontend Documentation (English)

## 1. Project Overview
The frontend delivers the BIOTech Futures Hub user experience: authentication, dashboards, collaboration, resource management, and administrator tooling. It is built with Vue 3 and Vite, using Pinia for state management and the Fetch API for backend communication.

- Key capabilities:
  - Passwordless login flow (magic link + OTP) aligned with the backend.
  - Role-aware navigation surfaced through a unified dashboard.
  - Group workspace including milestones, task tracking, and real-time style chat.
  - Resource, event, and announcement browsers with admin upload/publishing features.
  - Dedicated admin console for statistics, user CRUD, CSV export, and status workflows.
  - GSAP-powered page transitions and a modern design system implemented with global CSS tokens.

| Area                  | Technology / Service                            |
|-----------------------|--------------------------------------------------|
| Framework             | Vue 3 (Composition API, `<script setup>`)        |
| Build tool            | Vite 7                                           |
| State management      | Pinia 3                                          |
| Router                | Vue Router 4 (hash history)                      |
| Animation             | GSAP 3 + custom `AnimatedContent` component      |
| UI styling            | Custom CSS design tokens in `src/assets/styles.css` |
| API access            | Fetch API with JWT bearer tokens                 |
| Dev tooling           | ESLint 9, Prettier 3, Vite Vue Devtools plugin   |

## 2. Tooling & Runtime
- **Required Node version:** `^20.19.0` or `>=22.12.0` (see `engines` in `package.json`).
- **Package manager:** npm (lockfile committed).
- **Key scripts:**
  - `npm run dev` – start Vite dev server (hot module replacement on `localhost:5173` by default).
  - `npm run build` – generate production bundle in `frontend/dist`.
  - `npm run preview` – serve built assets locally for smoke testing.
  - `npm run lint` – run ESLint with auto-fix.
  - `npm run format` – format Vue/JS sources via Prettier.
- **Vite DevTools:** enabled through `vite-plugin-vue-devtools` for component inspection in development.

## 3. Directory Structure
```
frontend/
├── index.html                 # Vite application shell
├── vite.config.js             # Vite + plugin configuration, alias `@` -> `src`
├── src/
│   ├── main.js                # Vue app bootstrapping
│   ├── App.vue                # Root layout, navigation, animation wrapper
│   ├── router/                # Vue Router setup & auth guard
│   ├── stores/                # Pinia stores (auth, groups, resources, admin, etc.)
│   ├── views/                 # Page-level components mapped to routes
│   ├── components/            # Reusable UI elements (AnimatedContent)
│   ├── assets/                # Global styles + brand assets
│   ├── utils/                 # Shared helpers (`safeJson`)
│   └── data/mock.js           # Mock data placeholders (legacy/testing only)
├── public/                    # Static assets copied verbatim at build time
└── dist/                      # Build output (generated)
```

## 4. Application Architecture
### 4.1 Boot sequence
`src/main.js` creates the Vue app, installs Pinia and the router, hydrates the auth store from `localStorage`, and mounts the root component. Global styling is imported from `src/assets/styles.css`.

### 4.2 Layout & navigation
- `App.vue` renders the persistent header, sidebar navigation, notification panel, and the routed content area wrapped in `AnimatedContent` for GSAP entrance animations.
- The layout hides the chrome on `/login`, presenting a full-screen authentication flow.
- Navigation entries toggle automatically on role (e.g., Admin Panel appears only for admins).

### 4.3 Routing
- Defined in `src/router/index.js` using `createWebHashHistory`, which simplifies static hosting (no server-side rewrite rules required).
- Routes:
  - `/login` – passwordless authentication
  - `/dashboard` – role-aware landing page
  - `/groups` & `/groups/:id`
  - `/resources` & `/resources/:id` (detail view reuses same component)
  - `/events`
  - `/announcements`
  - `/profile`
  - `/admin` (admin console)
  - Fallback redirects unknown paths to `/login`
- Global navigation guard (`beforeEach`) hydrates the auth store, blocks access to private pages without a session, and re-routes signed-in users away from the login page.

### 4.4 State management (Pinia)
Each feature domain has its own store with caching, loading states, and error handling. Stores automatically reset when the signed-in user changes, preserving per-user caches.

| Store file                | Responsibility & notable methods                                                                                                        |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| `auth.js`                 | Handles magic-link requests, OTP verification, JWT storage/refresh, `authenticatedFetch`, session persistence in `localStorage`.        |
| `groups.js`               | Fetches personal/all groups, caches per-user data, loads group detail, milestone/task CRUD integration with backend endpoints.         |
| `chat.js`                 | Manages per-group message feeds, pagination (`hasMore`), message sending, and uploads via `/uploads/`.                                  |
| `resources.js`            | Lists accessible resources, admin-only creation/cover upload/delete, maps backend payloads to UI-friendly objects.                      |
| `events.js`               | Fetches upcoming events, admin creation, cover updates, attendee registration state, deletion.                                          |
| `announcements.js`        | Loads announcements by audience, admin publishing.                                                                                      |
| `admin.js`                | Admin stats, filters, user CRUD, CSV export, detail cache, and async status transitions.                                                |
| `announcements.js`        | Caches announcements and supports admin creation.                                                                                       |
| `events.js`               | Handles event browsing, admin creation, cover updates, and attendee registration.                                                       |

All network calls funnel through `auth.authenticatedFetch`, which injects the bearer token and retries once on HTTP 401 by refreshing the session. `safeJson` defends against empty responses.

### 4.5 API integration
- `VITE_API_BASE_URL` (or default `http://127.0.0.1:8000/api`) determines the backend origin.
- Endpoints mirror backend routing (see `docs/API.md`), e.g., `/auth/magic-link/`, `/users/me/`, `/groups/…`, `/resources/…`, `/admin/users/…`.
- Stores expect camelCase data but gracefully handle snake_case via mapping helpers.
- Fetch errors are surfaced as `Error` objects so UI layers can display messages.

### 4.6 UI system & animations
- Design tokens (colors, spacing, shadows, radii) live in `src/assets/styles.css`. Components reference CSS variables to maintain consistency.
- Font Awesome classes deliver icons (relies on CDN or global load in `index.html`).
- `AnimatedContent.vue` wraps sections to play GSAP entrance animations triggered by intersection observers; props allow tuning direction, distance, opacity, and repeat behaviour.

### 4.7 Data lifecycle & caching
- Stores track `loading`, `error`, and `listLoaded` flags to avoid duplicate requests.
- `auth.setSession` detects account switching and clears down-stream caches (groups/resources/events/announcements) to prevent stale data.
- Components typically call their store `fetch…` methods on `onMounted` and watch for user/role changes to refresh.
- The chat store merges messages client-side, deduplicating by `id` after sending or loading additional history.

## 5. Feature Overview

| View (`src/views`)           | Purpose & Behaviour                                                                                                                                                 |
|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `LoginPage.vue`             | Magic-link login UI. Sends link + OTP, manages 6-digit input, persists pending email, and redirects to dashboard after verification.                                |
| `DashboardPage.vue`         | Unified landing page showing groups, events, resources, and announcements tailored to role. Admins see global counts; watchers refresh data on auth changes.         |
| `GroupsPage.vue`            | Table of groups. Admins load all groups, others load assigned groups. Clicking a row navigates to `GroupDetailPage`.                                                 |
| `GroupDetailPage.vue`       | Two-column workspace: left for milestones/tasks (with add/delete/toggle actions), right for chat with attachment support. Includes responsive tabs for mobile.       |
| `ResourcesPage.vue`         | Resource gallery with filters by type/role, card layout, download links. Admins can upload new resources or change covers.                                           |
| `EventsPage.vue`            | Lists upcoming events, surfaces registration state, and exposes admin create/delete/cover actions.                                                                   |
| `AnnouncementsPage.vue`     | Displays announcements filtered by user audience; admins may publish new announcements.                                                                              |
| `ProfilePage.vue`           | Allows users to update track and nested profile fields (mirrors backend serializer contract).                                                                        |
| `AdminPage.vue`             | Rich dashboard featuring statistics by track, user table with bulk actions, filters, CRUD forms, CSV export, and status updates. Uses multiple store operations.    |

## 6. Admin Workflows
- **Statistics:** `admin.fetchStats` drives the hero cards (total users, mentors, students, active groups) filtered by track (`Global` + backend-provided tracks).
- **User table:** Supports search, track/role/status filters, inline status update, edit modal, delete, and CSV export. UI state flags (`usersLoading`, `savingUser`, `updatingStatus`) power button disablement and spinners.
- **CSV export:** Response blob and filename parsed from `Content-Disposition`, leaving file saving responsibility to the caller (currently triggered from UI).

## 7. Environment & Configuration
- Define environment overrides in `.env.local` (ignored by Git) using Vite’s `VITE_*` convention, e.g.:
  ```
  VITE_API_BASE_URL=https://api.biotechfutures.org/api
  VITE_APP_TITLE=BIOTech Futures Hub
  ```
- Hash-based routing means the app can be deployed behind any base path without server rewrite rules.
- Static assets placed under `public/` are served from the app root (`/`), useful for favicons or manifest files.
- Production builds assume the backend sets CORS to allow the frontend origin.

## 8. Development Workflow
1. `cd frontend`
2. `npm install`
3. Duplicate `.env.example` if created, or set `VITE_API_BASE_URL` manually.
4. `npm run dev` to start the app; Vite proxies API calls directly to the backend origin defined above.
5. During development, use Vite DevTools and browser Vue Devtools to inspect component state.

### Quality tooling
- ESLint config (`eslint.config.js`) extends Vue + Prettier defaults. Fix warnings before committing.
- Prettier is restricted to `src/` via `npm run format`.
- No dedicated unit tests yet; consider using Vitest + Vue Test Utils for future coverage.

## 9. Build & Deployment
- `npm run build` outputs a hashed asset bundle in `dist/` (HTML + JS + CSS). Host the directory via any static server (e.g., Nginx, Netlify, Vercel).
- Ensure the backend API base URL is reachable from the deployed domain and set `VITE_API_BASE_URL` before building.
- If co-hosting with the backend (e.g., Django serving frontend), copy the `dist/` assets into the backend static directory and configure Django to serve `index.html`.
- Because routing uses hash history, 404s do not require server-side rewrites; the fragment never reaches the server.

## 10. Troubleshooting
- **Blank screen after login:** Verify `VITE_API_BASE_URL` points to the correct backend and responds with CORS headers. Check the browser console for 401s caused by missing HTTPS or wrong host.
- **Stale data after switching accounts:** Session resets should clear caches. If issues persist, verify `auth.setSession` still imports dependent stores (avoid circular imports when refactoring).
- **File upload failures:** Confirm `/api/uploads/` accepts the file size/type and that the backend storage is correctly configured. The UI surfaces errors returned by the API.
- **Animations not playing:** `IntersectionObserver` powers `AnimatedContent`. On very old browsers, the component falls back to immediate animation via GSAP.
- **Font Awesome icons missing:** Ensure the icon font is imported globally (e.g., via CDN in `index.html`). Without it, placeholders render as empty squares.

## 11. Reference
- Backend integration contract: `docs/API.md`
- Backend architecture: `docs/backend-overview.en.md`
- Chinese localisation: `docs/frontend-overview.zh.md`

_Last updated: October 23, 2025_
