# BIOTech Futures Hub - API Documentation

**Version:** 1.0.0  
**Base URL:** `https://api.biotechfutures.org/v1`  
**Authentication:** Bearer Token (JWT)

---

## Authentication

### Request Magic Link
```http
POST /api/auth/magic-link
Content-Type: application/json

{
  "email": "student@example.com"
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Magic link sent to your email"
}
```

---

### Verify OTP Code
```http
POST /api/auth/verify-otp
Content-Type: application/json

{
  "email": "student@example.com",
  "code": "123456"
}
```

**Response 200:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "student@example.com",
    "role": "student",
    "track": "AUS-NSW"
  }
}
```

---

### Verify Magic Link
```http
GET /api/auth/verify?token={token}
```

**Response 200:** Same as verify OTP

---

### Refresh Token
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "..."
}
```

**Response 200:**
```json
{
  "token": "new_jwt_token"
}
```

---

## User Management

### Get Current User
```http
GET /api/users/me
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "id": 2,
  "name": "Yilin Guo",
  "email": "yilin.guo@email.com",
  "role": "student",
  "track": "AUS-NSW",
  "profile": {
    "firstName": "Yilin",
    "lastName": "Guo",
    "areasOfInterest": ["Biomedical Innovations", "AI & Robotics"],
    "schoolName": "Sydney High School",
    "yearLevel": 11,
    "country": "Australia",
    "region": "NSW"
  }
}
```

---

### Update Profile
```http
PUT /api/users/me
Authorization: Bearer {token}
Content-Type: application/json

{
  "profile": {
    "areasOfInterest": ["Biomedical Innovations"],
    "availability": "Weekends preferred"
  }
}
```

**Response 200:**
```json
{
  "success": true,
  "user": { /* updated user */ }
}
```

---

### List All Users (Admin)
```http
GET /api/admin/users?track=AUS-NSW&role=student&page=1&limit=20
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "results": [
    {
      "id": 2,
      "name": "Yilin Guo",
      "email": "yilin.guo@email.com",
      "role": "student",
      "track": "AUS-NSW",
      "status": "active"
    }
  ],
  "count": 180,
  "next": "http://api.../users?page=2",
  "previous": null
}
```

---

## Group Management

### Get My Groups
```http
GET /api/groups/my-groups
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "groups": [
    {
      "id": "BTF046",
      "name": "BTF046",
      "members": 4,
      "status": "Schedule Event",
      "mentor": {
        "id": 1,
        "name": "Anita Pickard"
      },
      "track": "AUS-NSW"
    }
  ]
}
```

---

### Get Group Details
```http
GET /api/groups/{groupId}
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "id": "BTF046",
  "name": "BTF046",
  "members": [
    {
      "id": 1,
      "name": "Anita Pickard",
      "role": "mentor"
    }
  ],
  "milestones": [
    {
      "id": 1,
      "title": "Getting Started",
      "tasks": [
        {
          "id": 11,
          "name": "Determine Group Topic",
          "completed": false
        }
      ]
    }
  ]
}
```

---

### Update Task
```http
PUT /api/groups/{groupId}/tasks/{taskId}
Authorization: Bearer {token}
Content-Type: application/json

{
  "completed": true
}
```

**Response 200:**
```json
{
  "success": true,
  "task": {
    "id": 11,
    "completed": true
  }
}
```

---

### Add Task
```http
POST /api/groups/{groupId}/milestones/{milestoneId}/tasks
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "New task name"
}
```

**Response 201:**
```json
{
  "id": 24,
  "name": "New task name",
  "completed": false
}
```

---

## Chat & Messages

### Get Messages
```http
GET /api/groups/{groupId}/messages?limit=50&before=2025-09-15T10:00:00Z
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "messages": [
    {
      "id": 1,
      "author": {
        "id": 1,
        "name": "Anita Pickard"
      },
      "text": "Hi team!",
      "timestamp": "2025-09-03T15:04:00Z",
      "attachments": []
    }
  ],
  "hasMore": false
}
```

---

### Send Message
```http
POST /api/groups/{groupId}/messages
Authorization: Bearer {token}
Content-Type: application/json

{
  "text": "Let's meet tomorrow!"
}
```

**Response 201:**
```json
{
  "id": 3,
  "author": {
    "id": 2,
    "name": "You"
  },
  "text": "Let's meet tomorrow!",
  "timestamp": "2025-09-15T14:40:00Z"
}
```

---

### Upload File
```http
POST /api/uploads
Authorization: Bearer {token}
Content-Type: multipart/form-data

file=@document.pdf
```

**Response 201:**
```json
{
  "url": "https://storage.example.com/files/abc123.pdf",
  "filename": "document.pdf",
  "size": 102400
}
```

---

## Resources

### List Resources
```http
GET /api/resources?type=document&role=all&search=guidebook
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "results": [
    {
      "id": 1,
      "title": "2025 Challenge Guidebook",
      "type": "document",
      "role": "all",
      "url": "https://storage.../guidebook.pdf",
      "coverImage": null
    }
  ],
  "count": 8
}
```

---

### Get Resource Details
```http
GET /api/resources/{id}
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "id": 1,
  "title": "2025 Challenge Guidebook",
  "description": "Complete guide",
  "type": "document",
  "url": "https://storage.../guidebook.pdf"
}
```

---

### Upload Resource (Admin)
```http
POST /api/resources
Authorization: Bearer {token}
Content-Type: multipart/form-data

title=New Resource
type=document
role=all
file=@resource.pdf
```

**Response 201:**
```json
{
  "id": 9,
  "title": "New Resource",
  "url": "https://storage.../resource.pdf"
}
```

---

## Events

### List Events
```http
GET /api/events?type=virtual&upcoming=true
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "results": [
    {
      "id": 1,
      "title": "Program Kickoff",
      "date": "2025-09-15",
      "time": "10:00 AM",
      "location": "Sydney University",
      "type": "in-person",
      "coverImage": null
    }
  ]
}
```

---

### Get Event Details
```http
GET /api/events/{id}
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "id": 1,
  "title": "Program Kickoff",
  "description": "Join us!",
  "date": "2025-09-15",
  "time": "10:00 AM",
  "location": "Sydney University",
  "type": "in-person"
}
```

---

### Register for Event
```http
POST /api/events/{id}/register
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Successfully registered"
}
```

---

## Announcements

### List Announcements
```http
GET /api/announcements?audience=all&search=welcome
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "results": [
    {
      "id": 101,
      "title": "Welcome to 2025 Challenge",
      "summary": "Kickoff details",
      "author": "Program Team",
      "audience": "all",
      "date": "2025-09-01T09:00:00Z"
    }
  ]
}
```

---

### Get Announcement Details
```http
GET /api/announcements/{id}
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "id": 101,
  "title": "Welcome",
  "content": "Full content...",
  "author": "Program Team",
  "date": "2025-09-01T09:00:00Z"
}
```

---

## Admin Dashboard

### Get Statistics
```http
GET /api/admin/stats?track=AUS-NSW
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "totalUsers": 250,
  "activeGroups": 45,
  "mentors": {
    "total": 50,
    "active": 48
  },
  "students": {
    "total": 180
  }
}
```

---

### Update User Status (Admin)
```http
PUT /api/admin/users/{userId}/status
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "active"
}
```

**Response 200:**
```json
{
  "success": true,
  "user": {
    "id": 2,
    "status": "active"
  }
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

**Common Status Codes:**
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Server Error

---

**Last Updated:** October 14, 2025