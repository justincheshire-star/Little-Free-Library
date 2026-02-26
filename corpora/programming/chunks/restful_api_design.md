---
title: "RESTful API Design Principles"
domain: "programming"
subdomain: "web-development"
source: "REST API Design Best Practices"
source_license: "CC-BY"
source_id: "rest-api-guide-2024"
source_path: "design-principles"
retrieved_at: "2026-02-26"
verified: "2026-02-26"
importance: 0.9
tags: ["rest", "api", "web", "http", "design"]
version: "1.0.0"
content_hash: "sha256:placeholder"
---

# RESTful API Design Principles

REST (Representational State Transfer) is an architectural style for designing networked applications. A RESTful API uses HTTP requests to access and manipulate data.

## Core Principles

### 1. Resource-Based URLs

URLs should represent resources (nouns), not actions (verbs):

**Good:**
```
GET    /users          # Get all users
GET    /users/123      # Get user 123
POST   /users          # Create new user
PUT    /users/123      # Update user 123
DELETE /users/123      # Delete user 123
```

**Bad:**
```
GET  /getUsers
POST /createUser
POST /updateUser
GET  /deleteUser?id=123
```

### 2. HTTP Methods

Use appropriate HTTP methods:

- **GET**: Retrieve resource(s) - idempotent, safe
- **POST**: Create new resource
- **PUT**: Update existing resource (full replacement)
- **PATCH**: Partial update of resource
- **DELETE**: Remove resource

### 3. Status Codes

Return appropriate HTTP status codes:

**Success:**
- 200 OK: Successful GET, PUT, PATCH, or DELETE
- 201 Created: Successful POST
- 204 No Content: Successful request with no response body

**Client Errors:**
- 400 Bad Request: Invalid syntax
- 401 Unauthorized: Authentication required
- 403 Forbidden: Authenticated but not authorized
- 404 Not Found: Resource doesn't exist
- 409 Conflict: Request conflicts with current state

**Server Errors:**
- 500 Internal Server Error: Generic server error
- 503 Service Unavailable: Temporary unavailability

### 4. Versioning

Include API version in the URL:
```
/api/v1/users
/api/v2/users
```

### 5. Pagination

For collections, implement pagination:
```
GET /api/v1/users?page=2&limit=50
```

Response should include:
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 50,
    "total": 1000,
    "pages": 20
  }
}
```

### 6. Filtering and Sorting

```
GET /api/v1/users?status=active&sort=-created_at&fields=id,name,email
```

## Security Best Practices

- Always use HTTPS
- Implement authentication (OAuth 2.0, JWT)
- Rate limiting to prevent abuse
- Validate all inputs
- Use API keys for tracking and access control
