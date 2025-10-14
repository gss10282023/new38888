# BIOTech Futures Hub (new38888)

This repository currently hosts a Vue 3 + Vite front-end that showcases BIOTech Futures Hub interfaces and user flows. The sections below explain the project structure, the role of each major directory/file, and how to continue building on top of it.

## Stack & Local Development
- Node.js: recommended `^20.19.0` (enforced in `package.json`)
- Front-end framework: Vue 3, Pinia, Vue Router
- Build tooling: Vite
- Code quality: ESLint (Vue rules + Prettier integration)

Getting started:
```bash
cd website
npm install
npm run dev
```

## Directory Overview
```text
new38888/
├── README.md                # Chinese overview
├── README.en.md             # English overview (this file)
├── package-lock.json        # Dependency lock file preserved at the repo root
└── website/                 # Front-end application code
    ├── README.md            # Vite template instructions
    ├── package.json         # website sub-project scripts and dependencies
    ├── package-lock.json
    ├── index.html           # Vite entry HTML
    ├── vite.config.js       # Vite config (adds @ alias, Vue DevTools plugin)
    ├── eslint.config.js     # ESLint Flat config
    ├── jsconfig.json        # IDE path aliases
    ├── public/
    │   └── favicon.ico      # Default favicon
    └── src/                 # Vue source code
        ├── main.js          # App entry, mounts Vue, Pinia, router
        ├── App.vue          # Global layout (header, sidebar, notification panel)
        ├── router/
        │   └── index.js     # Route definitions + auth guard
        ├── stores/
        │   └── auth.js      # Pinia auth store with localStorage hydration
        ├── data/
        │   └── mock.js      # Mock data for users, groups, resources, events, announcements
        ├── assets/
        │   ├── styles.css   # Global styles (brand palette, layout, shared components)
        │   ├── logo.svg
        │   └── btf-logo.png
        └── views/           # Page-level Vue components
            ├── LoginPage.vue
            ├── DashboardPage.vue
            ├── GroupDetailPage.vue
            ├── ResourcesPage.vue
            ├── EventsPage.vue
            ├── AnnouncementsPage.vue
            ├── ProfilePage.vue
            ├── AdminPage.vue
            └── AboutView.vue
```

## Key Directories & Files

### Repository Root
- `README.md`: Chinese project overview.
- `README.en.md`: English project overview.
- `package-lock.json`: Locks dependency versions to keep installations stable across environments.
- `website/`: Houses all front-end source code and build configuration.

### website Sub-Project
- `package.json`: Declares dependencies (Vue, Pinia, Vue Router) and scripts (`dev`, `build`, `lint`, `format`).
- `vite.config.js`: Sets the `@` alias to `src/` and enables `vite-plugin-vue-devtools` for debugging.
- `eslint.config.js`: ESLint Flat config combining `eslint-plugin-vue` rules with Prettier's skip-formatting preset.
- `jsconfig.json`: Provides the same `@` alias to editors/IDE tooling.
- `index.html`: Vite entry template with the `#app` mount point.
- `public/favicon.ico`: Default site icon, replace with brand-specific artwork if needed.
- `README.md`: Default instructions from the Vite starter template.

### src Directory
- `main.js`: Boots the Vue application, registers Pinia and the router, imports global styles, and hydrates the auth state from `localStorage`.
- `App.vue`: Root component that renders the global layout: header, sidebar navigation, notification panel, and conditional routing based on auth state.
- `router/index.js`: Declares routes for login, dashboard, resources, events, announcements, group details, profile, admin-panel, and catches unmatched paths; includes an auth guard that redirects guests to `/login` and logged-in users away from `/login`.
- `stores/auth.js`: Pinia store with login/logout helpers, admin role checks, initials for the avatar, and local persistence using `mockUsers`.
- `data/mock.js`: Centralized mock data set containing:
  - `mockUsers`: Sample users with role, track, and status
  - `mockGroups`: Team/group information
  - `mockResources`: Resource entries with type and audience
  - `mockEvents`: Upcoming event schedule
  - `mockAnnouncements`: Announcement feed with audience targeting and links
- `assets/styles.css`: Global styling assets defining branding colors, typography, layout primitives, buttons, cards, and notification styles shared by all pages.
- `assets/logo.svg` / `btf-logo.png`: Brand imagery used throughout the UI.

### View Components (`src/views`)
- `LoginPage.vue`: Split layout login page with program introduction on the left and an email + OTP simulation form on the right.
- `DashboardPage.vue`: Post-login landing dashboard showing a welcome message, group/event/announcement metrics, group cards, and highlighted resources powered by mock data.
- `GroupDetailPage.vue`: Group workspace with a “Plan” column for milestone tracking and a “Discussion” column for message threads.
- `ResourcesPage.vue`: Resource library supporting search, filtering by type, and admin-only cover image management (uploads stored as DataURL).
- `EventsPage.vue`: Event listing featuring cover image controls, a details modal, and registration CTAs; admins can upload covers or add new events.
- `AnnouncementsPage.vue`: Announcement feed with full-text search, audience labels, and optional internal/external links.
- `ProfilePage.vue`: Profile management page displaying user info with interactive sections for interests, contact preferences, and availability.
- `AdminPage.vue`: Admin dashboard with key metrics and a user management table including search, bulk selection, export, and add-user actions (demo interactions).
- `AboutView.vue`: Placeholder view kept from the starter template for future use.

## Future Enhancements
- Replace `mock.js` with real API integrations once backend services are available.
- Hook the OTP login flow into actual authentication endpoints and improve error handling/user feedback.
- Introduce live data updates (e.g., WebSocket or polling) for collaboration features in `GroupDetailPage` and admin metrics.
- Add unit tests and end-to-end coverage to protect core user journeys as the project matures.
