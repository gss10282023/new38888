# BIOTech Futures Hub – Backend Documentation (English)

## 1. Project Overview
The backend powers the BIOTech Futures Hub platform, exposing authenticated REST APIs for program administration, group collaboration, announcements, events, resources, and chat.  
It is a Django 5.1 project that uses Django REST Framework (DRF) for API delivery, PostgreSQL for relational data, Redis for caching/magic-link OTP storage, and S3-compatible object storage for uploaded files.

- Key capabilities:
  - Passwordless authentication using magic links and one-time codes.
  - Role-based access control spanning students, mentors, supervisors, and admins.
  - Group lifecycle management (creation, membership, milestones, tasks).
  - Real-time collaboration features such as chat message streams with attachments.
  - Event, resource, and announcement distribution with audience targeting.
  - Admin analytics, CSV exports, and filter metadata for console dashboards.

| Component            | Technology / Service                     |
|----------------------|-------------------------------------------|
| Web framework        | Django 5.1 (Python 3.13 ready)            |
| API layer            | Django REST Framework 3.15                |
| Auth                 | JWT (djangorestframework-simplejwt) + magic links |
| Database             | PostgreSQL (psycopg2-binary)              |
| Cache / OTP storage  | Redis via django-redis                    |
| Object storage       | Vultr Object Storage (S3-compatible via django-storages + boto3) |
| Email                | django-anymail (default console backend locally) |
| API schema           | drf-spectacular (Swagger/Redoc endpoints) |
| Deployment runtime   | Gunicorn (production WSGI server)         |

## 2. Repository Layout
Top-level structure (trimmed to backend-relevant paths):

```
backend/
├── authentication/     # Magic link + JWT issuance
│   ├── urls.py         # Public auth endpoints
│   └── views.py        # Token issuance, OTP logic
├── users/              # User & profile management + admin endpoints
│   ├── admin_urls.py   # Admin dashboard routes
│   ├── serializers.py  # CamelCase payload mapping
│   └── views.py        # ViewSets for self-service + admin tools
├── groups/             # Team management, milestones, tasks
│   ├── serializers.py  # Nested milestone/task representations
│   └── views.py        # Scoped access + admin actions
├── chat/               # Group-scoped messaging & attachments
├── resources/          # Resource library CRUD & file handling
├── events/             # Event listings, registration, cover uploads
├── announcements/      # Audience-filtered announcements
├── core/               # Health check, uploads, shared permissions
├── btf_backend/        # Project settings, urls, WSGI/ASGI entrypoints
├── media/              # Local media uploads (development)
├── requirements.txt    # Python package constraints
├── manage.py           # Django CLI entry point
└── scripts/            # Utility scripts (e.g., add users to a group)
```

Each app follows DRF best practices—models, serializers, viewsets/plain views, and URL routers. Global URL dispatching lives in `backend/btf_backend/urls.py`.

## 3. Settings & Environment
Key settings are defined in `backend/btf_backend/settings.py` with `.env` overrides loaded via `python-dotenv`.

Important environment variables:

| Variable | Description | Development default |
|----------|-------------|---------------------|
| `SECRET_KEY` | Django secret key. Required in production. | `django-insecure-default-key-change-in-production` |
| `DEBUG` | `"True"` / `"False"`. Controls debug mode and health-check output. | `True` |
| `ALLOWED_HOSTS` | Comma-separated hostnames for Django. | `localhost,127.0.0.1` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection. | `btf_db`, `btf_user`, `""`, `localhost`, `5432` |
| `REDIS_URL` | Redis connection string (e.g. `redis://127.0.0.1:6379/1`). | `redis://127.0.0.1:6379/1` |
| `CHANNEL_REDIS_URL` | Optional WebSocket pub/sub Redis endpoint for Django Channels; falls back to `REDIS_URL` or in-memory channel layer locally. | unset |
| `FRONTEND_BASE_URL` | Used when constructing magic-link callback URLs. | `https://yourdomain.com` |
| `MAGIC_LINK_EXPIRY_SECONDS` | TTL in seconds for magic link & OTP (default 600). | `600` |
| `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL`, `EMAIL_HOST`, ... | Email delivery configuration. | Console backend |
| `VULTR_ACCESS_KEY`, `VULTR_SECRET_KEY`, `VULTR_BUCKET_NAME`, `VULTR_S3_ENDPOINT` | Object storage credentials (used by `django-storages`). | unset (filesystem storage) |
| `JWT_ACCESS_TOKEN_LIFETIME_HOURS`, `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Overrides for JWT expiry windows. | `1`, `7` |
| `CORS_ALLOW_ALL_ORIGINS` / `CORS_ALLOWED_ORIGINS` | CORS configuration for the frontend. | `http://localhost:5173` |

Environment profiles:
- **Development:** `DEBUG=True`, console email backend, local filesystem storage, optional SQLite fallback when running tests.
- **Staging:** Mirror production with reduced quotas; use distinct Redis database and bucket prefixes to avoid collisions.
- **Production:** `DEBUG=False`, hardened `ALLOWED_HOSTS`, TLS-enabled email/object storage endpoints, and rotated secret keys.

Static files are collected into `staticfiles/`; media uploads live under `media/` when using the default filesystem backend. In production, `DEFAULT_FILE_STORAGE` should point to the S3 backend.

## 4. Authentication & Authorization Flow
1. **Magic link request** (`POST /api/auth/magic-link/`): normalizes email, validates format, stores OTP + token in Redis, and sends both link + OTP via email.  
2. **OTP verification** (`POST /api/auth/verify-otp/`) or **link verification** (`GET /api/auth/verify/`): exchanges OTP/token for JWT pair. A new `User` + `UserProfile` is provisioned automatically if the email does not already exist.  
3. **JWT refresh** (`POST /api/auth/refresh/`): issues a fresh access/refresh token pair.  
4. **Authorization**: DRF enforces JWT authentication globally; only the magic-link & health-check endpoints allow anonymous access.

Failure modes & safeguards:
- Expired tokens/OTPs return HTTP 400 with user-friendly messaging; tokens are cleared from Redis after successful verification.
- Repeated OTP validation attempts are limited by Redis TTL; consider rate limiting at the API gateway for added resilience.
- Newly created users have unusable passwords to enforce passwordless login, preventing fallback to username/password.

Token payloads include `role`, `track`, and `status` claims via the serialized user object, enabling the frontend to adjust UX without extra round-trips.

Roles (`users.User.role`) drive business permissions:
- `student`, `mentor`, `supervisor`: standard participants.
- `admin`: platform administrator (grants `IsPlatformAdmin` permission).
- `is_staff` / `is_superuser`: Django admin flags; superusers automatically satisfy admin checks.

## 5. Core Application Modules
### authentication
- Stateless OTP + magic-link login.
- Issues JWTs via `rest_framework_simplejwt`.
- Relies on cache backend (Redis) for temporary token/OTP storage.
- Key endpoints: `/api/auth/magic-link/`, `/api/auth/verify-otp/`, `/api/auth/verify/`, `/api/auth/refresh/`.
- External calls: `django.core.mail.send_mail` (configurable via Anymail).
- Notable settings: `MAGIC_LINK_EXPIRY_SECONDS`, `FRONTEND_BASE_URL`.

### users
- Custom `User` model (email as username, role & status fields) and `UserProfile`.
- Endpoints for self-serve profile updates (`/api/users/me/`) and admin CRUD (`/api/admin/users/`).
- Admin-specific helpers: stats, CSV export, dynamic filters.
- Serializers convert snake_case model fields to camelCase API payloads.
- CSV export streams responses directly using `HttpResponse` to avoid writing to disk.
- Business rules: admins cannot delete themselves or superusers; status updates validate against `STATUS_CHOICES`.

### groups
- Models: `Group`, `GroupMember`, `Milestone`, `Task`.
- Features: scoped access (admins see everything, others see joined groups), milestone creation/deletion, task creation & completion toggles, group creation/deletion for admins.
- Serializer mixins provide human-friendly names for mentor/member display.
- Access helper `_user_can_manage_group` centralises permission checks for milestone/task operations.
- Group IDs can be supplied explicitly (`groupId`) or generated automatically (`BTF###`).
- Query optimisation: `select_related` for mentors, `prefetch_related` for members/milestones/tasks.

### chat
- Models: `Message`, `MessageAttachment`.
- Endpoints: list, paginated backwards with `before` cursor; create messages with optional attachment metadata (files are stored separately via `/api/uploads/`).
- Access control mirrors group membership rules.
- Cursor-style pagination is implemented manually with `limit` + `before`; `hasMore` flags when additional records are available.
- Attachments expect pre-uploaded file URLs (no binary upload through chat endpoints).

### resources
- Model: `Resource` (typed assets, optional cover image, download count).
- Endpoints: list, retrieve, admin-only create/delete, cover image updates (S3 upload).
- Enforces audience filtering by role (`all`, `student`, `mentor`, `supervisor`, `admin`).
- Upload flow: files handled via `MultiPartParser`, stored through Django's storage backend, then persisted as a URL.
- Cover updates use a separate PUT endpoint to avoid resending metadata.

### events
- Models: `Event`, `EventRegistration`.
- Admins can create/delete events and upload cover images.
- Participants can browse, filter, and register; duplicate registrations return a 400 response.
- `upcoming=true` filters by event date >= today; registration counts are annotated via `Count`.
- Registrations enforce uniqueness (`unique_together`) at the database level.

### announcements
- Model: `Announcement` with audience targeting.
- Admins manage announcements; non-admins only receive `audience == all` plus their own role.
- Search filters across `title`, `summary`, and `content`.
- `audience` constants align with frontend filters (`all`, `student`, `mentor`, `supervisor`, `admin`).

### core
- `health_check`: verifies PostgreSQL & Redis connectivity; returns HTTP 503 if any check fails.
- `upload_file`: authenticated file upload endpoint storing assets via configured storage backend.
- `permissions.IsPlatformAdmin`: shared DRF permission class.
- Middleware-friendly utilities should live here (e.g., pagination defaults, future storage helpers).

## 6. Data Model Highlights
- `users.User` extends `AbstractUser` with role/status/track fields and enforces unique email login.
- `users.UserProfile` stores extended metadata (areas of interest, availability, etc.) as camelCase in the API layer.
- `groups.Group` uses a string primary key (e.g., `BTF046`) to match BIOTech Futures naming conventions.
- `chat.MessageAttachment` persists metadata only; actual content is hosted in object storage.
- `resources.Resource.download_count` is reserved for future increment logic when downloads are tracked.

Entity relationships (simplified):

```
User (custom auth)
 ├─1:1─ UserProfile
 ├─1:M─ Group (mentor)                Group
 ├─M:N─ GroupMember ── M:1 ── Group    │
 │                                     ├─1:M─ Milestone ──1:M─ Task
 ├─1:M─ Message (chat author)          │
 ├─1:M─ MessageAttachment (through Message)
 ├─1:M─ EventRegistration ── M:1 ── Event
 └─1:M─ Resource (created_by TBD)
```

All timestamp fields (`created_at`, `updated_at`) use UTC and auto-update via Django model defaults.

Soft deletion is not implemented; deletions cascade according to `on_delete` rules (`CASCADE` for memberships/tasks, `SET_NULL` for mentor references).

Refer to `docs/API.md` for field-level API schemas.

## 7. External Integrations
- **Email**: default console backend locally; configure Anymail (SendGrid/Mailgun/etc.) via environment variables for production.
- **Object Storage**: `django-storages` + `boto3`; uploaded files and covers are saved under the `uploads/`, `resources/files/`, `resources/covers/`, and `events/covers/` prefixes.
- **Redis**: used for magic-link tokens and general caching. Ensure Redis is reachable before allowing logins.
- **Realtime messaging (Channels)**: group chat WebSocket fan-out uses Django Channels. Configure `CHANNEL_REDIS_URL` (or reuse `REDIS_URL`) so background workers share the same Redis instance.
- **DRF Spectacular**: generates OpenAPI schema consumed by Swagger/Redoc UIs; customise via `SPECTACULAR_SETTINGS`.
- **Django Admin**: available at `/admin/` for superusers; use for raw data inspection and migrations.

## 8. Local Development Workflow
1. **Install dependencies**
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Configure `.env`** (copy from the table in section 3). For local development you can use SQLite/console email by omitting DB/Redis vars, but OTP delivery will also log to console.
3. **Apply migrations**
   ```bash
   python manage.py migrate
   ```
4. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```
5. **Run the server**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
6. **Run tests**
   ```bash
   python manage.py test
   ```

Helper shell scripts:
- `backend/install_dependencies.sh` – installs system-level prerequisites (used in CI/bootstrap).
- `backend/setup_database.sh` – guides PostgreSQL user/db creation.
- `backend/scripts/add_users_to_group.py` – quick utility to seed a group with users via Django shell.
- `backend/scripts/smoke_step*.sh` – legacy smoke scripts for quickly verifying core modules; review/update as needed.

## 9. Deployment Notes
- Use Gunicorn (or another WSGI server) to run `btf_backend.wsgi:application`.
- Serve static files via CDN or web server (`collectstatic` required).
- Configure environment variables for PostgreSQL, Redis, object storage, and email providers.
- Enable HTTPS and set `ALLOWED_HOSTS`.
- When running under DEBUG=False, ensure proper logging and storage credentials are in place; otherwise uploads or magic-link emails will fail.
- Recommended infrastructure stack: reverse proxy (NGINX) -> Gunicorn -> Django app. Offload TLS termination and compression at the proxy layer.
- Database migrations should run as part of the deployment pipeline (`python manage.py migrate`).
- Collect static assets to object storage or a CDN-friendly bucket and invalidate caches after releases.

## 10. Operations & Monitoring
- **Health Check**: `/api/health/` verifies database and cache. Integrate this endpoint with uptime monitoring; HTTP 503 indicates degraded dependencies.
- **OpenAPI Docs**: `/api/docs/` (Swagger UI) and `/api/redoc/` (ReDoc) provide live documentation generated by drf-spectacular.
- **Caching**: Redis TTL determines validity of magic link tokens. Monitor Redis availability closely.
- **Logging**: Authentication flow logs OTP/magic-link issuance (`authentication.views`). Configure Django logging handlers as needed in production.
- **Metrics**: Consider exporting request metrics via middleware (not yet implemented). Gunicorn access logs provide baseline analytics.
- **Backups**: Schedule PostgreSQL dumps and Redis snapshots. Uploaded files should rely on storage-provider versioning.

## 11. Known Limitations / Future Enhancements
- Download counting for resources is not yet wired to an endpoint.
- Event updates currently disallow PUT/PATCH; extending partial updates will require serializer changes.
- Magic-link email template is plaintext only; consider HTML templates for production.
- No background task queue is configured; long-running jobs (e.g., bulk mail) would require Celery or RQ if introduced.
- Rate limiting and brute-force protection rely on upstream infrastructure; evaluate DRF throttling or API gateway policies.
- File uploads assume S3 public-access URLs; add signed URL support if private ACLs are needed.

## 12. Reference
- Detailed HTTP contract: `docs/API.md`
- Frontend views (Vue): `frontend/src/views/` (useful for understanding expected payload shapes)

## 13. Request Lifecycle & Middleware
1. **Incoming request** hits Django via Gunicorn (prod) or the development server.
2. **Middleware stack** processes CORS headers, sessions, security checks, CSRF (for admin), and authentication.
3. **DRF** handles content negotiation, authentication (`JWTAuthentication`), permission checks, throttling (default none), and view dispatch.
4. **Serializers** validate request payloads and transform database objects into JSON responses.
5. **Response** passes back through middleware (adding CORS headers) before being returned to the client.

Key middleware:
- `corsheaders.middleware.CorsMiddleware` – handles CORS preflight and headers.
- `django.middleware.security.SecurityMiddleware` – enforces HTTPS redirect and security headers when configured.
- DRF paginates responses via `PageNumberPagination`; override `page_size` via query parameters.

## 14. Security Considerations
- **Transport security:** Require HTTPS in production; update `SECURE_SSL_REDIRECT` if fronting with TLS proxy.
- **JWT secrets:** Rotate `SECRET_KEY` when compromised; tokens are signed using HS256.
- **CORS:** Tighten `CORS_ALLOWED_ORIGINS` to trusted frontend hosts only.
- **Admin endpoints:** Guarded by `IsPlatformAdmin`; ensure admin accounts use secure emails.
- **Uploads:** Validate MIME types as needed; current implementation trusts uploaded file types. Consider virus scanning for production.
- **Email abuse:** Magic link endpoint can be abused for enumeration; monitor request rates and introduce captcha/rate limiting if exposed publicly.

## 15. Testing Strategy
- **Unit tests:** Each app defines tests under `<app>/tests.py`. Extend with additional modules (e.g., `tests/` directory) for better organisation.
- **Integration tests:** Use DRF's `APIClient` to simulate full request flows, including JWT issuance.
- **Management commands:** For scripts like `add_users_to_group`, leverage Django's `call_command` within tests.
- **Continuous integration:** Run `python manage.py test` and optional linting (flake8/black) before deploying.
- **Fixtures:** Create JSON fixtures for deterministic data (e.g., sample groups) when writing integration tests.

## 16. Data Seeding & Sample Accounts
- Use `backend/scripts/add_users_to_group.py` to create placeholder users/groups during demos.
- Magic link flow can bootstrap new accounts quickly; combine with environment variables pointing to a staging SMTP relay for testing.
- Consider adding management commands for bulk CSV import of users, events, or resources as future work.

## 17. Troubleshooting & Support
- **Cannot connect to PostgreSQL:** Verify credentials, ensure the database user exists (`setup_database.sh`), and confirm network/VPC firewall rules.
- **Redis errors in health check:** Check Redis availability; when missing, authentication will reject OTP verification.
- **File uploads failing:** Inspect storage credentials and bucket permissions. In development, ensure `MEDIA_ROOT` is writable.
- **Emails not delivered:** With console backend, messages appear in server logs. For real SMTP, confirm SPF/DKIM and Anymail configuration.
- **JWT invalid signature:** Ensure all servers share the same `SECRET_KEY`; restart Gunicorn after rotations.

_Last updated: October 24, 2025_
