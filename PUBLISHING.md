# Publishing checklist (Phase 5)

This file is a practical checklist for the final “public release” steps in `OPEN_SOURCE_PLAN.md`.

## 1) GitHub repository About (copy/paste)

**Description (EN)**  
Passwordless, role-based collaboration hub for project-based programs (Django + Vue).

**Topics (minimum)**  
`django`, `vue`, `vite`, `channels`, `drf`, `postgres`, `redis`

**Homepage**  
Set to your deployment URL (e.g. Vercel/Netlify for frontend + Render/Railway for backend), such as:  
`https://YOUR-PROJECT.example`

**Optional**  
- Set a Social preview image (GitHub repo Settings → Social preview).

## 2) README badges

Ensure the build status badge points to the correct GitHub repo and workflow file:
- `README.md`

If you rename the repository, update the badge URL and link target accordingly.

## 3) Release v1.0.0

**Before you tag**
- Ensure `CI` is green on `main`.
- Ensure `gitleaks` is green on `main`.
- Double-check no secrets are committed (especially any `.env`).

**Create a tag**
```bash
git tag -a v1.0.0 -m "v1.0.0"
git push origin v1.0.0
```

**Create GitHub release notes**
- Use `docs/release-notes/v1.0.0.md` as the release body.
- Recommended title: `v1.0.0`

If you use GitHub CLI:
```bash
gh release create v1.0.0 -F docs/release-notes/v1.0.0.md
```
