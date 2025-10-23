# BIOTech Futures Hub – API Reference

**Version:** 1.0.0  
**Base Path:** `/api/` (prepend with your deployment origin, e.g. `https://hub.example.com/api/`)  
**Authentication:** Bearer access token (JWT) issued by the authentication endpoints.

---

## Conventions
- All endpoints return JSON unless otherwise stated. File exports use their native content type.
- Trailing slashes are required (Django REST Framework default routing).
- Timestamps are ISO-8601 strings in UTC. Booleans appear as lowercase `true` / `false`.
- Unless explicitly marked as public, endpoints require a valid `Authorization: Bearer <access_token>` header.
- Pagination uses DRF's `PageNumberPagination` with `page` and `page_size` query parameters (default 20).

---

## Authentication

### Request Magic Link
`POST /api/auth/magic-link/`

*Permissions:* Public  
*Body:*
```json
{ "email": "student@example.com" }
```

*Response 200:*
```json
{
  "success": true,
  "message": "Magic link sent to your email."
}
```

### Verify OTP Code
`POST /api/auth/verify-otp/`

*Permissions:* Public  
*Body:*
```json
{
  "email": "student@example.com",
  "code": "123456"
}
```

*Response 200:*
```json
{
  "token": "access-token",
  "refresh_token": "refresh-token",
  "user": {
    "id": 2,
    "email": "student@example.com",
    "username": "student@example.com",
    "role": "student",
    "track": "AUS-NSW",
    "status": "active",
    "name": "Yilin Guo",
    "profile": {
      "firstName": "Yilin",
      "lastName": "Guo",
      "areasOfInterest": ["Biomedical Innovations", "AI & Robotics"],
      "controlledInterests": ["Medical Devices"],
      "schoolName": "Sydney High School",
      "yearLevel": 11,
      "country": "Australia",
      "region": "NSW",
      "availability": "Weekends preferred",
      "bio": "",
      "guardianEmail": "parent@example.com",
      "supervisorEmail": "admin@example.com",
      "joinPermissionGranted": true
    },
    "supervisorProfile": null,
    "supervisors": [
      {
        "id": 12,
        "relationshipType": "guardian",
        "joinPermissionGranted": true,
        "joinPermissionGrantedAt": "2025-02-01T11:30:00Z",
        "notes": "Guardian approval received 2025-02-01",
        "supervisor": {
          "id": 31,
          "email": "guardian@example.com",
          "role": "supervisor",
          "track": "",
          "status": "active",
          "name": "Casey Guardian",
          "supervisorProfile": {
            "organization": "Example School",
            "phoneNumber": "+61 400 000 000",
            "wwccNumber": "WWCC123456",
            "wwccExpiry": "2026-06-30",
            "wwccVerified": true,
            "createdAt": "2025-01-01T10:00:00Z",
            "updatedAt": "2025-04-15T10:30:00Z"
          }
        }
      }
    ],
    "supervisees": []
  }
}
```

### Verify Magic Link
`GET /api/auth/verify/?token=<magic_token>`

*Permissions:* Public  
*Response 200:* identical to *Verify OTP Code*.

### Refresh Token
`POST /api/auth/refresh/`

*Permissions:* Public  
*Body:*
```json
{ "refresh_token": "refresh-token" }
```

*Response 200:*
```json
{
  "token": "new-access-token",
  "refresh_token": "new-refresh-token"
}
```

---

## Users

### Get Current User
`GET /api/users/me/`

*Permissions:* Authenticated  
*Response 200:* Same payload as in *Verify OTP Code* → `user`. The response exposes:

- `profile`: student-facing information including guardian contact details (`guardianEmail`, `supervisorEmail`) and the `joinPermissionGranted` toggle captured during onboarding.
- `supervisorProfile`: compliance details for supervisors/mentors (organisation, WWCC number/expiry, phone). `null` when the signed-in user is a student.
- `supervisors`: relationships where the signed-in user is the student, including relationship type, join-permission status, and the linked supervisor's summary profile.
- `supervisees`: relationships where the signed-in user supervises other students (empty for students).

### Update Current User
`PUT /api/users/me/` or `PATCH /api/users/me/`

*Permissions:* Authenticated  
*Body Example (partial update):*
```json
{
  "track": "Global",
  "profile": {
    "areasOfInterest": ["Synthetic Biology"],
    "availability": "Weekdays 17:00–20:00",
    "controlledInterests": ["AI & Data Science"],
    "guardianEmail": "guardian@example.com",
    "joinPermissionGranted": true
  },
  "supervisorProfile": {
    "organization": "Innovation High School",
    "phoneNumber": "+61 400 000 000",
    "wwccNumber": "WWCC123456",
    "wwccExpiry": "2026-06-30"
  }
}
```

*Response 200:* Updated user document (same structure as *Get Current User*).

---

### List My Supervisor Relationships
`GET /api/users/me/supervisors/`

*Permissions:* Authenticated  
Returns the relationships where the signed-in user participates either as a student or as a supervisor/mentor. Standard pagination (`page`, `page_size`) applies.

*Response 200 (paginated):*
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 12,
      "student": {
        "id": 2,
        "email": "student@example.com",
        "role": "student",
        "track": "AUS-NSW",
        "status": "active",
        "name": "Yilin Guo",
        "supervisorProfile": null
      },
      "supervisor": {
        "id": 31,
        "email": "guardian@example.com",
        "role": "supervisor",
        "track": "",
        "status": "active",
        "name": "Casey Guardian",
        "supervisorProfile": {
          "organization": "Example School",
          "phoneNumber": "+61 400 000 000",
          "wwccNumber": "WWCC123456",
          "wwccExpiry": "2026-06-30",
          "wwccVerified": true,
          "createdAt": "2025-01-01T10:00:00Z",
          "updatedAt": "2025-04-15T10:30:00Z"
        }
      },
      "relationshipType": "guardian",
      "joinPermissionGranted": true,
      "joinPermissionGrantedAt": "2025-02-01T11:30:00Z",
      "notes": "Guardian approval received 2025-02-01",
      "createdAt": "2025-01-15T04:12:00Z",
      "updatedAt": "2025-02-01T11:30:00Z"
    }
  ]
}
```

### Toggle Join Permission
`PATCH /api/users/me/supervisors/{id}/`

*Permissions:* Authenticated (relationship participant)  
Updates the `joinPermissionGranted` flag for the specified relationship. Only users involved in the relationship (student or supervisor) may call the endpoint.

*Body:*
```json
{ "joinPermissionGranted": true }
```

*Response 200:* Updated relationship object (same structure as list response).

---

## Admin Dashboard (Requires `role=admin` or Django superuser)

### High-Level Statistics
`GET /api/admin/stats/?track=<track|global>`

*Response 200:*
```json
{
  "totalUsers": 250,
  "activeGroups": 45,
  "mentors": {
    "total": 50,
    "active": 48,
    "pending": 2
  },
  "students": {
    "total": 180,
    "pending": 12
  }
}
```

### List Users
`GET /api/admin/users/`

*Query:* `role`, `track`, `status`, `search`, `page`, `page_size`  
*Response 200 (paginated):*
```json
{
  "count": 32,
  "next": "https://hub.example.com/api/admin/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": 2,
      "name": "Yilin Guo",
      "email": "student@example.com",
      "role": "student",
      "track": "AUS-NSW",
      "status": "active"
    }
  ]
}
```

### Create User
`POST /api/admin/users/`

*Body Example:*
```json
{
  "email": "mentor@example.com",
  "role": "mentor",
  "track": "AUS-NSW",
  "status": "pending",
  "profile": {
    "firstName": "Alex",
    "lastName": "Nguyen",
    "areasOfInterest": ["Bioinformatics"]
  }
}
```

*Response 201:*
```json
{
  "id": 6,
  "name": "Alex Nguyen",
  "email": "mentor@example.com",
  "role": "mentor",
  "track": "AUS-NSW",
  "status": "pending"
}
```

### Retrieve / Update / Delete User
- `GET /api/admin/users/<id>/` → 200 with full `User` document.
- `PUT /api/admin/users/<id>/` or `PATCH /api/admin/users/<id>/` → 200 with full `User` document.
- `DELETE /api/admin/users/<id>/` → 204 (forbidden when attempting to delete self or a superuser).

### Update User Status
`PUT /api/admin/users/<id>/status/`

*Body:* `{ "status": "active" }`  
*Response 200:*
```json
{
  "success": true,
  "user": {
    "id": 2,
    "name": "Yilin Guo",
    "email": "student@example.com",
    "role": "student",
    "track": "AUS-NSW",
    "status": "active"
  }
}
```

### Filter Metadata
`GET /api/admin/users/filters/` → lists distinct `tracks`, plus available `roles` and `statuses`.

### Export Filtered Users
`GET /api/admin/users/export/`

*Response:* CSV attachment (`text/csv`) containing the filtered dataset with full profile columns.

### Manage Student–Supervisor Links
- `GET /api/admin/student-supervisors/` → list relationships (supports `studentId`, `supervisorId`, `relationshipType`, pagination).
- `POST /api/admin/student-supervisors/` → create a new link.
- `PATCH /api/admin/student-supervisors/<id>/` → update relationship metadata or toggle join permission.
- `DELETE /api/admin/student-supervisors/<id>/` → remove a link.

*Create Body Example:*
```json
{
  "studentId": 2,
  "supervisorId": 31,
  "relationshipType": "guardian",
  "joinPermissionGranted": true,
  "notes": "Guardian approval received 2025-02-01"
}
```

*List Response (paginated):* same structure as *List My Supervisor Relationships*.

---

## Groups

All group endpoints require authentication. Administrative actions (create, delete) require platform admin rights. Milestone/task management is allowed for admins, supervisors, group mentors, and group members.

### List Accessible Groups
`GET /api/groups/`

*Query:* `track`, `status`  
*Response 200:*
```json
{
  "groups": [
    {
      "id": "BTF046",
      "name": "Microfluidics Innovators",
      "members": 4,
      "status": "active",
      "mentor": { "id": 3, "name": "Anita Pickard" },
      "track": "AUS-NSW"
    }
  ]
}
```

### List My Groups
`GET /api/groups/my-groups/`

Returns groups where the requester is a member or mentor. Response matches *List Accessible Groups*.

### Retrieve Group Details
`GET /api/groups/<group_id>/`

*Response 200:*
```json
{
  "id": "BTF046",
  "name": "Microfluidics Innovators",
  "members": [
    { "id": 3, "name": "Anita Pickard", "role": "mentor" },
    { "id": 2, "name": "Yilin Guo", "role": "student" }
  ],
  "status": "active",
  "mentor": { "id": 3, "name": "Anita Pickard" },
  "track": "AUS-NSW",
  "milestones": [
    {
      "id": 11,
      "title": "Getting Started",
      "description": "Kick-off checklist",
      "order_index": 1,
      "tasks": [
        { "id": 101, "name": "Determine project topic", "completed": false }
      ]
    }
  ]
}
```

### Create Group (Admin)
`POST /api/groups/`

*Body Example:*
```json
{
  "groupId": "BTF120",
  "name": "BioSensors United",
  "track": "Global",
  "status": "active",
  "mentorId": 8,
  "members": [
    { "userId": 8, "role": "mentor" },
    { "userId": 12, "role": "student" },
    { "userId": 14, "role": "student" }
  ]
}
```

*Response 201:* Full group detail (same shape as *Retrieve Group Details*).

### Delete Group (Admin)
`DELETE /api/groups/<group_id>/` → 204.

### Create Milestone
`POST /api/groups/<group_id>/milestones/`

*Body:* `{ "title": "Research Plan", "description": "Outline hypotheses." }`  
*Response 201:* Milestone document.

### Delete Milestone
`DELETE /api/groups/<group_id>/milestones/<milestone_id>/` → 204.

### Add Task
`POST /api/groups/<group_id>/milestones/<milestone_id>/tasks/`

*Body:* `{ "name": "Submit ethics form" }`  
*Response 201:* `{ "id": 205, "name": "Submit ethics form", "completed": false }`

### Update Task Completion
`PUT /api/groups/<group_id>/tasks/<task_id>/`

*Body:* `{ "completed": true }`  
*Response 200:* `{ "success": true, "task": { "id": 205, "name": "Submit ethics form", "completed": true } }`

---

## Chat

### List Messages
`GET /api/groups/<group_id>/messages`

*Query:* `limit` (default 50, max 100), `before` (ISO timestamp for pagination)  
*Response 200:*
```json
{
  "messages": [
    {
      "id": 301,
      "author": { "id": 2, "name": "Yilin Guo" },
      "text": "Let's meet tomorrow!",
      "timestamp": "2025-03-15T14:40:00Z",
      "attachments": [
        {
          "file_url": "https://storage.example.com/files/slides.pdf",
          "filename": "slides.pdf",
          "file_size": 102400,
          "mime_type": "application/pdf"
        }
      ],
      "isDeleted": false,
      "deletedAt": null,
      "deletedBy": null,
      "moderation": {
        "status": "approved",
        "note": null,
        "moderatedAt": null,
        "moderatedBy": null
      }
    }
  ],
  "hasMore": false
}
```

Non-moderators will only see active messages; removed or rejected content is
suppressed automatically.

### Send Message
`POST /api/groups/<group_id>/messages`

*Body Example:*
```json
{
  "text": "Agenda draft attached.",
  "attachments": [
    {
      "url": "https://storage.example.com/files/agenda.docx",
      "filename": "agenda.docx",
      "size": 56320,
      "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }
  ]
}
```

*Response 201:* Message document (same structure as in *List Messages*).

### Moderate Message
`PATCH /api/groups/<group_id>/messages/<message_id>`

*Permissions:* Group mentor, supervisor, platform admin, or staff.  
*Body Example:*
```json
{
  "moderationStatus": "rejected",
  "moderationNote": "Removed due to inappropriate language"
}
```

Setting `restore: true` in the payload clears a previous soft delete. Response
returns the updated message document.

### Soft Delete Message
`DELETE /api/groups/<group_id>/messages/<message_id>`

Marks the message as deleted without removing it from the database. The
response (200) returns the updated message record (`isDeleted: true`), which is
only visible to moderators.

### Realtime Updates

`ws/chat/groups/<group_id>/` — JWT-authenticated WebSocket endpoint. Clients
receive `message.created`, `message.updated`, and `message.deleted` events with
the same payload shape as the REST responses. Supply the access token via the
`token` query parameter, e.g. `ws://localhost:8000/ws/chat/groups/BTF046/?token=<jwt>`.

---

## Core Utilities

### Health Check
`GET /api/health/`

*Permissions:* Public  
*Response 200:*
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "redis": "connected"
  },
  "environment": {
    "debug": "False",
    "django_version": "5.1.1"
  }
}
```

If a dependency fails, the endpoint returns HTTP 503 with `status: "unhealthy"` and diagnostic messages.

### Upload File
`POST /api/uploads/`

*Permissions:* Authenticated  
*Content-Type:* `multipart/form-data` with `file` field.  
*Response 201:*
```json
{
  "url": "https://storage.example.com/uploads/a1b2c3.pdf",
  "filename": "proposal.pdf",
  "size": 102400,
  "mimeType": "application/pdf"
}
```

Files are validated for size, extension, and optionally scanned via the
configured antivirus command. Suspicious uploads return HTTP 400 with an error
descriptor and are not persisted.

---

## Resources Library

### List Resources
`GET /api/resources/`

*Query:* `type`, `role`, `search`, `page`, `page_size`  
*Response 200:*
```json
{
  "count": 8,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 11,
      "title": "2025 Challenge Guidebook",
      "type": "document",
      "role": "all",
      "url": "https://storage.example.com/resources/files/guidebook.pdf",
      "coverImage": null
    }
  ]
}
```

### Retrieve Resource
`GET /api/resources/<id>/`

*Response 200:*
```json
{
  "id": 11,
  "title": "2025 Challenge Guidebook",
  "type": "document",
  "role": "all",
  "url": "https://storage.example.com/resources/files/guidebook.pdf",
  "coverImage": null,
  "description": "Complete guide to the 2025 challenge.",
  "download_count": 125,
  "created_at": "2025-02-01T05:00:00Z",
  "updated_at": "2025-02-10T03:12:00Z"
}
```

### Upload Resource (Admin)
`POST /api/resources/`

*Body:* multipart form with `title`, optional `description`, `type`, `role`, and `file`.  
*Response 201:* Full resource document (same as *Retrieve Resource*).

### Delete Resource (Admin)
`DELETE /api/resources/<id>/` → 204.

### Update Resource Cover (Admin)
`PUT /api/resources/<id>/cover/`

*Body:* multipart form with `coverImage`.  
*Response 200:* `{ "coverImage": "https://storage.example.com/resources/covers/cover.png" }`

---

## Events

### List Events
`GET /api/events/`

*Query:* `type`, `upcoming` (`true`/`false`), `search`, `page`, `page_size`  
*Response 200:*
```json
{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 21,
      "title": "Program Kickoff",
      "description": "Launch event overview.",
      "date": "2025-09-15",
      "time": "10:00 AM",
      "location": "Sydney University",
      "type": "in-person",
      "coverImage": null,
      "registerLink": "https://events.example.com/register/21",
      "capacity": 200,
      "createdAt": "2025-08-20T00:00:00Z",
      "updatedAt": "2025-08-20T00:00:00Z",
      "isRegistered": false,
      "registrationCount": 85
    }
  ]
}
```

### Retrieve Event
`GET /api/events/<id>/`

*Response 200:* Same fields as list plus `longDescription`.

### Create Event (Admin)
`POST /api/events/`

*Body Example:*
```json
{
  "title": "Industry Mentor Q&A",
  "description": "Short teaser",
  "longDescription": "Extended agenda and speaker list...",
  "date": "2025-10-05",
  "time": "18:00 AEST",
  "location": "Online",
  "type": "virtual",
  "registerLink": "https://events.example.com/register/22",
  "capacity": 500
}
```

*Response 201:* Event detail document.

### Delete Event (Admin)
`DELETE /api/events/<id>/` → 204.

### Register for Event
`POST /api/events/<id>/register/`

*Response 201 (created):*
```json
{ "success": true, "message": "Successfully registered" }
```

*Response 400 (already registered):*
```json
{ "success": false, "message": "Already registered" }
```

### Update Event Cover (Admin)
`PUT /api/events/<id>/cover/`

*Body:* multipart form with `coverImage`.  
*Response 200:* `{ "coverImage": "https://storage.example.com/events/covers/cover.png" }`

---

## Announcements

### List Announcements
`GET /api/announcements/`

*Query:* `audience`, `search`, `page`, `page_size`  
*Response 200:*
```json
{
  "count": 12,
  "next": "https://hub.example.com/api/announcements/?page=2",
  "previous": null,
  "results": [
    {
      "id": 101,
      "title": "Welcome to 2025 Challenge",
      "summary": "Key kickoff information",
      "content": "Full announcement body...",
      "author": "Program Team",
      "audience": "all",
      "link": "https://example.com/blog/welcome",
      "createdAt": "2025-09-01T09:00:00Z",
      "updatedAt": "2025-09-01T09:00:00Z"
    }
  ]
}
```

Audience filtering is automatic: students/mentors/supervisors receive only `audience` `all` plus their role; admins see all.

### Retrieve Announcement
`GET /api/announcements/<id>/`

*Response 200:* Announcement document.

### Create Announcement (Admin)
`POST /api/announcements/`

*Body:* `{ "title": "...", "summary": "...", "content": "...", "author": "Program Team", "audience": "mentor", "link": "https://..." }`  
*Response 201:* Announcement document.

### Delete Announcement (Admin)
`DELETE /api/announcements/<id>/` → 204.

---

## API Schema & Developer Tools

- `GET /api/schema/` – raw OpenAPI 3 schema (JSON).
- `GET /api/docs/` – Swagger UI.
- `GET /api/redoc/` – ReDoc UI.

---

## Error Format

Unless specified otherwise, validation and permission errors follow one of the standard DRF payloads:

```json
{ "error": "Human readable message." }
```

or field-mapped errors:
```json
{ "field": ["Validation message."] }
```

Common status codes:
- `400 Bad Request` – validation or malformed data.
- `401 Unauthorized` – missing or invalid JWT.
- `403 Forbidden` – insufficient permissions (e.g., non-admin on admin route).
- `404 Not Found` – resource missing or inaccessible.
- `409 Conflict` – occasionally returned for state conflicts (e.g., duplicate operations).
- `500 Internal Server Error` – unhandled exceptions.

---

**Last Updated:** October 23, 2025
