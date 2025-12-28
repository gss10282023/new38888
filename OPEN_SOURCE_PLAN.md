# BIOTech Futures Hub – Open Source Readiness Plan (English)

Goal: prepare this repository for a public open-source release: reproducible local setup, no secrets, and a clear product narrative.

## Success criteria

### Security & privacy
- No usable secrets (keys, passwords, tokens) exist in the repository **or its git history**.
- Secret scanning (gitleaks and/or GitHub Secret Scanning) reports no high-severity findings.

### Open-source usability
- A new contributor can start the full stack locally using the README (frontend + backend + Postgres + Redis).
- CI runs reliably on PRs and main branch pushes.

### External narrative
- The README shows UI previews (screenshots/GIFs) on the first screen.
- Documentation does not include course/homework/teamwork traces.

---

## Phase 0 (must do first): Rotate secrets + clean history

1. Rotate any leaked credentials (SMTP provider, S3/object storage keys, `SECRET_KEY`).
2. Keep real secrets out of git:
   - commit only `.env.example` files
   - ensure `.env` is ignored (root `.gitignore`)
3. If any secret ever entered git history (even if later deleted):
   - **Preferred:** publish from a clean repo with a fresh history.
   - **Alternative:** rewrite history using `git filter-repo` and force-push (coordinate with collaborators).
4. Ensure secret scanning is enabled:
   - `gitleaks` workflow in `.github/workflows/`
   - optionally enable GitHub Secret Scanning in repository settings

---

## Phase 1: Repo hygiene (“de-homework”)

- Remove private/internal planning docs and any personal identifiers.
- Rename internal scripts to neutral, operations-friendly names (e.g. `smoke_*.sh`).
- Ensure non-source artifacts are ignored (editor folders, OS files, `node_modules/`, media uploads).

---

## Phase 2: README + preview assets

- Keep `README.md` as the canonical English README.
- Store preview images under `docs/assets/preview/` and reference them from the README.

---

## Phase 3: One-command reproducible dev

- Provide Docker Compose for Postgres/Redis/backend/frontend.
- Provide demo seed data to make screenshots and UI exploration reproducible.

---

## Phase 4: Open-source infrastructure

- Add `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`.
- Add CI:
  - backend: Django tests
  - frontend: lint, test, build
- Keep secret scanning on PRs (gitleaks).

---

## Phase 5: Publishing

See:
- `PUBLISHING.md`
- `docs/release-notes/v1.0.0.md`
