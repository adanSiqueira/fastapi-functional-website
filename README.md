<div align="center">

# FastAPI Blog

<br/>

![Python](https://img.shields.io/badge/Python-3.14+-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?style=for-the-badge&logo=databricks&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-RDS-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Jinja2](https://img.shields.io/badge/Jinja2-Templates-black?style=for-the-badge&logo=jinja&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![AWS](https://img.shields.io/badge/AWS-ECS%20%7C%20RDS%20%7C%20S3-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**Live:** https://fa-9d583b6d064346df8c5d8fa8ba6ac60b.ecs.us-east-2.on.aws/

</div>

---

A full-stack blog application built with **FastAPI**, deployed on **AWS ECS**, backed by **AWS RDS PostgreSQL**, and using **AWS S3** for media storage. The app exposes both:

- A **REST API** (`/api/...`) for programmatic access
- A **server-rendered website** via **Jinja2 templates** with vanilla JS for dynamic interactions

The codebase is designed as a reusable blueprint for systems requiring user accounts, authentication, content creation, and full CRUD — adaptable to forums, news platforms, social feeds, and more.

---

## Table of Contents

1. [Features](#features)
2. [Architecture Overview](#architecture-overview)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Data Models](#data-models)
6. [Pydantic Schemas](#pydantic-schemas)
7. [Authentication & Security](#authentication--security)
8. [API Reference](#api-reference)
9. [Web Routes](#web-routes)
10. [Frontend Architecture](#frontend-architecture)
11. [Image Handling (S3)](#image-handling-s3)
12. [Email & Password Reset](#email--password-reset)
13. [Database & Migrations](#database--migrations)
14. [Configuration](#configuration)
15. [Docker & Deployment](#docker--deployment)
16. [Running Locally](#running-locally)
17. [Testing](#testing)
18. [Security Headers](#security-headers)
19. [Health Check](#health-check)

---

## Features

### Web Application (Jinja2 + Bootstrap)

- Homepage with paginated posts (server-rendered first page, "Load More" via JS fetch)
- Single post page with edit/delete controls (owner-only, resolved via JWT)
- Per-user post listing page with infinite scroll
- Navbar dynamically shows Login/Register vs. Username/Account based on auth state
- Bootstrap modals for creating, editing, and deleting posts
- Account settings page: update profile, upload/delete profile picture, change password, delete account
- Forgot password / reset password pages
- Light / Dark / Auto theme toggle (persisted in `localStorage`)
- Custom HTML error pages for all HTTP errors (404, 422, 500, etc.)
- PWA-ready (`site.webmanifest`, icons, theme color)

### REST API

- Full CRUD for **Users** and **Posts**
- JWT Bearer token authentication
- Paginated post listings with `skip` / `limit` / `has_more`
- Profile picture upload (multipart) and deletion
- Password change (authenticated) and password reset (token-based, via email)
- 202 Accepted on forgot-password to prevent email enumeration

### Infrastructure

- Deployed on **AWS ECS** (containerized via Docker)
- **AWS RDS PostgreSQL** as the primary database
- **AWS S3** for profile picture storage
- Alembic for database schema migrations
- Health check endpoint for container orchestration

---

## Architecture Overview

```
Browser
  │
  ├── GET /  → Jinja2 renders home.html (SSR posts)
  │             └── JS fetches /api/posts for "Load More"
  │
  ├── POST /api/users/token → JWT issued
  │             └── token stored in localStorage
  │
  └── All /api/* endpoints → FastAPI routers
            ├── auth.py (JWT + password hashing)
            ├── routers/users.py
            └── routers/posts.py
                      │
                      ├── SQLAlchemy async ORM → AWS RDS PostgreSQL
                      └── boto3 → AWS S3 (profile pictures)
```

Request flow for protected API endpoints:
1. Client sends `Authorization: Bearer <token>` header
2. `oauth2_scheme` extracts the token
3. `verify_access_token()` validates JWT signature, expiry, and required claims (`sub`, `exp`)
4. `get_current_user()` loads the user from the database to confirm they still exist
5. The `CurrentUser` type alias injects the resolved `User` model into the endpoint

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI 0.128 |
| Language | Python 3.14 |
| ORM | SQLAlchemy 2.0 (async) |
| Database driver | asyncpg (PostgreSQL) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Password hashing | pwdlib (Argon2) |
| JWT | PyJWT |
| File storage | AWS S3 via boto3 |
| Image processing | Pillow |
| Email | aiosmtplib |
| ASGI server | Uvicorn |
| Templating | Jinja2 |
| Frontend styling | Bootstrap 5.3 |
| Frontend JS | Vanilla ES6 modules |
| Containerization | Docker (multi-stage) |
| Cloud hosting | AWS ECS |
| Database hosting | AWS RDS PostgreSQL |
| Testing | pytest + pytest-asyncio + httpx + moto |

---

## Project Structure

```
.
├── main.py                        # FastAPI app entrypoint, web routes, middleware, exception handlers
├── auth.py                        # JWT creation/verification, password hashing, CurrentUser dependency
├── config.py                      # Pydantic Settings (reads .env)
├── database.py                    # Async SQLAlchemy engine, session factory, Base, get_db dependency
├── models.py                      # SQLAlchemy ORM models: User, Post, PasswordResetToken
├── schemas.py                     # Pydantic request/response schemas
├── image_utils.py                 # S3 client, image processing (resize/crop/reformat), upload/delete helpers
├── email_utils.py                 # aiosmtplib email sender, password reset email builder
├── check_s3.py                    # CLI utility to verify S3 credentials and permissions
│
├── routers/
│   ├── posts.py                   # Posts API: CRUD endpoints
│   └── users.py                   # Users API: CRUD, auth, picture upload, password management
│
├── alembic/
│   ├── env.py                     # Alembic async migration environment
│   ├── script.py.mako             # Migration script template
│   └── versions/                  # Auto-generated migration files
│
├── templates/                     # Jinja2 HTML templates
│   ├── layout.html                # Base layout (navbar, modals, theme toggle, auth JS)
│   ├── home.html                  # Post feed with load-more pagination
│   ├── post.html                  # Single post view with edit/delete
│   ├── user_posts.html            # Posts by a specific user
│   ├── account.html               # Account settings (profile, picture, password, delete)
│   ├── login.html                 # Login form
│   ├── register.html              # Registration form
│   ├── forgot_password.html       # Forgot password form
│   ├── reset_password.html        # Reset password form (token from URL)
│   ├── error.html                 # Generic HTTP error page
│   └── email/
│       └── password_reset.html    # HTML email template for password resets
│
├── static/
│   ├── css/
│   │   └── main.css               # Custom CSS (CSS variables, dark mode, responsive)
│   ├── js/
│   │   ├── auth.js                # getCurrentUser, getToken, setToken, logout, clearUserCache
│   │   └── utils.js               # getErrorMessage, showModal, hideModal, escapeHtml, formatDate
│   ├── icons/                     # favicon.ico, icon.svg, icon.png
│   ├── profile_pics/
│   │   └── default.jpg            # Default avatar (used when no S3 image is set)
│   └── site.webmanifest           # PWA manifest
│
├── tests/
│   ├── conftest.py                # Fixtures: engine, DB session (with rollback), mocked S3, HTTPX client
│   ├── test_posts.py              # Post API tests
│   ├── test_users.py              # User API tests
│   └── test_image.jpg             # Sample image for upload tests
│
├── Dockerfile                     # Multi-stage Docker build
├── requirements.txt               # Pinned dependencies
├── alembic.ini                    # Alembic configuration
└── .env                           # Environment variables (not committed)
```

---

## Data Models

### User

```python
class User(Base):
    __tablename__ = "users"

    id: int                        # Primary key
    username: str                  # Unique, max 50 chars
    email: str                     # Unique, max 120 chars, stored lowercase
    password_hash: str             # Argon2 hash — never stored in plain text
    image_file: str | None         # S3 filename (e.g. "abc123.jpg"), None if no picture

    posts: list[Post]              # One-to-many, cascade delete
    reset_tokens: list[PasswordResetToken]  # One-to-many, cascade delete

    @property
    def image_path(self) -> str:
        # Returns full S3 URL if image_file is set, else /static/profile_pics/default.jpg
```

### Post

```python
class Post(Base):
    __tablename__ = "posts"

    id: int
    title: str                     # Max 100 chars
    content: str                   # Unlimited text
    user_id: int                   # FK → users.id (indexed)
    date_posted: datetime          # Timezone-aware UTC, auto-set on create
    likes: int                     # Default 0

    author: User                   # Many-to-one relationship
```

### PasswordResetToken

```python
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: int
    user_id: int                   # FK → users.id
    token_hash: str                # SHA-256 hash of the raw token (64 chars, unique)
    expires_at: datetime           # UTC expiry (configurable, default 60 min)
    created_at: datetime           # Auto-set on creation

    user: User
```

The raw token is **never stored** — only its SHA-256 hash. The plaintext token is sent to the user's email and then discarded.

---

## Pydantic Schemas

| Schema | Used For |
|---|---|
| `UserCreate` | `POST /api/users` — username, email, password (min 8 chars) |
| `UserUpdate` | `PATCH /api/users/{id}` — optional username and/or email |
| `UserPublicResponse` | Public user data: id, username, image_file, image_path |
| `UserPrivateResponse` | Extends public + adds email; returned to the authenticated user |
| `Token` | `access_token` + `token_type` for login response |
| `PostCreate` | `POST /api/posts` — title (optional, max 100), content (required) |
| `PostUpdate` | `PATCH /api/posts/{id}` — all fields optional |
| `PostResponse` | Full post: id, title, content, user_id, date_posted, author (UserPublicResponse) |
| `PaginatedPostsResponse` | posts list + total + skip + limit + has_more |
| `ForgotPasswordRequest` | email field |
| `ResetPasswordRequest` | token + new_password |
| `ChangePasswordRequest` | current_password + new_password |

---

## Authentication & Security

### Password Hashing

Passwords are hashed using **Argon2** via `pwdlib`. The hash string contains the algorithm identifier, salt, and digest — it is stored in the `password_hash` column. Plain-text passwords are never persisted.

```python
hash_password(password: str) -> str
verify_password(plain_password: str, hashed_password: str) -> bool
```

### JWT Tokens

Tokens are signed HS256 JWTs. The payload contains:
- `sub`: the user's integer ID (as a string)
- `exp`: expiration timestamp

```python
create_access_token(data: dict, expires_delta: timedelta | None) -> str
verify_access_token(token: str) -> str | None   # returns "sub" or None
```

Default expiry is configured via `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 30).

### Protected Endpoints

Use the `CurrentUser` type alias in any endpoint signature:

```python
@router.post("/api/posts")
async def create_post(post: PostCreate, current_user: CurrentUser, db: ...):
    ...
```

`CurrentUser` is defined as:

```python
CurrentUser = Annotated[models.User, Depends(get_current_user)]
```

`get_current_user` extracts and validates the Bearer token, then fetches the user from the database — ensuring deleted or inactive accounts are rejected even with a valid token.

### Frontend Auth State

JWT tokens are stored in `localStorage`. The `static/js/auth.js` module exposes:

```js
getCurrentUser()   // Fetches /api/users/me, caches result, deduplicates concurrent calls
getToken()         // Returns token from localStorage
setToken(token)    // Stores token in localStorage
logout()           // Removes token, clears cache, redirects to /
clearUserCache()   // Invalidates in-memory user cache (used after profile updates)
```

The base layout (`layout.html`) calls `getCurrentUser()` on every page load to toggle the logged-in vs. logged-out navbar.

### Authorization Rules

- Users can only update/delete **their own** account and posts (HTTP 403 otherwise)
- Post edit/delete buttons are rendered client-side only if `user.id === post.user_id`
- Profile picture upload/delete requires the authenticated user to match the target `user_id`

### Password Reset Flow

1. `POST /api/users/forgot-password` with `{email}` → always returns 202 (prevents enumeration)
2. If user exists: generates a `secrets.token_urlsafe(32)` token, stores its SHA-256 hash in `password_reset_tokens`, sends a reset email with the raw token in the URL
3. `POST /api/users/reset-password` with `{token, new_password}` → hashes the token, looks it up, checks expiry, updates password, deletes the token
4. Any existing reset tokens for a user are deleted before generating a new one

Reset tokens expire after `RESET_TOKEN_EXPIRE_MINUTES` (default: 60).

### Security Headers (applied to all responses)

| Header | Value |
|---|---|
| `X-Frame-Options` | `SAMEORIGIN` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains` (non-localhost only) |

The reset password page also sets `Referrer-Policy: no-referrer` to prevent the token leaking via the `Referer` header.

### Host Header Injection Prevention

The `frontend_url` used to construct password reset links is read from `.env` — it is **never derived from the incoming request's `Host` header**, which would be vulnerable to Host Header Injection attacks.

---

## API Reference

### Users — `POST /api/users`

Create a new user account.

**Request body:**
```json
{
  "username": "adan",
  "email": "adan@example.com",
  "password": "securepassword123"
}
```

**Response `201`:** `UserPrivateResponse` (id, username, email, image_file, image_path)

Fails with `400` if username or email already exists (case-insensitive check). Email is stored lowercase.

---

### Users — `POST /api/users/token`

Login and obtain a JWT access token.

**Request:** `application/x-www-form-urlencoded` (OAuth2 form)
```
username=adan@example.com&password=securepassword123
```

Note: the `username` field accepts the user's **email** (OAuth2PasswordRequestForm convention).

**Response `200`:**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

---

### Users — `GET /api/users/me` 🔒

Returns the currently authenticated user (`UserPrivateResponse`).

---

### Users — `GET /api/users`

Returns all users as `list[UserPublicResponse]`. Returns `404` if no users exist.

---

### Users — `GET /api/users/{user_id}`

Returns a single user by ID (`UserPublicResponse`). Returns `404` if not found.

---

### Users — `PATCH /api/users/{user_id}` 🔒

Partially update username and/or email for the authenticated user's own account.

**Request body (all fields optional):**
```json
{
  "username": "new_username",
  "email": "new@example.com"
}
```

Returns `403` if attempting to update another user. Returns `400` on duplicate username or email.

---

### Users — `DELETE /api/users/{user_id}` 🔒

Delete the authenticated user's account. Cascades to all their posts. Deletes their S3 profile picture if one exists. Returns `204`.

---

### Users — `PATCH /api/users/{user_id}/picture` 🔒

Upload a profile picture. Accepts `multipart/form-data` with a `file` field.

- Max size: `MAX_UPLOAD_SIZE_BYTES` (default: 5 MB)
- Accepted formats: JPEG, PNG, GIF, WebP
- Image is processed server-side: EXIF orientation corrected, cropped/resized to 300×300 px, saved as JPEG (quality 85)
- Stored in S3 under `profile_pics/<uuid>.jpg`
- Old image is deleted from S3 after successful upload

Returns `UserPrivateResponse` with updated `image_file` and `image_path`.

---

### Users — `DELETE /api/users/{user_id}/picture` 🔒

Delete the user's profile picture from S3 and set `image_file` to `null`. Returns `UserPrivateResponse`. Returns `400` if no picture exists.

---

### Users — `GET /api/users/{user_id}/posts`

Get paginated posts by a specific user.

**Query params:** `skip` (default 0), `limit` (default 10, max 100)

**Response:** `PaginatedPostsResponse`

---

### Users — `POST /api/users/forgot-password`

Request a password reset email.

**Request body:** `{"email": "user@example.com"}`

Always returns `202` regardless of whether the email exists.

---

### Users — `POST /api/users/reset-password`

Reset password using a valid token from the reset email.

**Request body:**
```json
{
  "token": "<raw_token_from_email>",
  "new_password": "newpassword123"
}
```

Returns `400` if token is invalid or expired.

---

### Users — `PATCH /api/users/me/password` 🔒

Change password for the currently authenticated user.

**Request body:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

Returns `400` if `current_password` is wrong. Invalidates all existing reset tokens on success.

---

### Posts — `GET /api/posts`

List all posts, ordered by most recent.

**Query params:** `skip` (default 0, min 0), `limit` (default 10, min 1, max 100)

**Response `200`:**
```json
{
  "posts": [...],
  "total": 42,
  "skip": 0,
  "limit": 10,
  "has_more": true
}
```

Each post in the list includes a nested `author` object (`UserPublicResponse`).

---

### Posts — `GET /api/posts/{post_id}`

Get a single post by ID. Returns `404` if not found. Note: the author relationship is **not** eagerly loaded on this endpoint (use the home or user_posts endpoints for author data).

---

### Posts — `POST /api/posts` 🔒

Create a new post.

**Request body:**
```json
{
  "title": "My Post Title",
  "content": "Post body content here."
}
```

Title is optional (max 100 chars). Content is required (min 1 char). The `user_id` is set automatically from the authenticated user. Returns `PostResponse` with `201`.

---

### Posts — `PUT /api/posts/{post_id}` 🔒

Full replacement update of a post. Both `title` and `content` are required. Returns `403` if not the post owner.

---

### Posts — `PATCH /api/posts/{post_id}` 🔒

Partial update of a post. Both fields are optional. Returns `403` if not the post owner.

---

### Posts — `DELETE /api/posts/{post_id}` 🔒

Delete a post. Returns `204`. Returns `403` if not the post owner.

---

> 🔒 = Requires `Authorization: Bearer <token>` header

---

## Web Routes

| Route | Template | Description |
|---|---|---|
| `GET /` | `home.html` | Post feed (SSR first page + JS load more) |
| `GET /site/posts` | `home.html` | Alias for home |
| `GET /posts/{post_id}` | `post.html` | Single post view |
| `GET /users/{user_id}/posts` | `user_posts.html` | Posts by a user |
| `GET /login` | `login.html` | Login form |
| `GET /register` | `register.html` | Registration form |
| `GET /account` | `account.html` | Account settings (auth required client-side) |
| `GET /forgot-password` | `forgot_password.html` | Forgot password form |
| `GET /reset-password` | `reset_password.html` | Reset password (token in query param) |

All web routes render `error.html` on HTTP errors; API routes return JSON.

---

## Frontend Architecture

The frontend is a hybrid: server-side rendering for initial content (fast first paint, SEO-friendly) with vanilla JavaScript ES6 modules for dynamic interactions.

### Module Structure

**`static/js/auth.js`** — Authentication state management
- `getCurrentUser()`: fetches `/api/users/me` with the stored token; caches the result and deduplicates in-flight requests
- `logout()`: clears localStorage token, resets cache, redirects to `/`
- `getToken()` / `setToken(token)` / `clearUserCache()`

**`static/js/utils.js`** — Shared UI utilities
- `getErrorMessage(error)`: extracts a human-readable string from FastAPI error responses (handles both string `detail` and array of validation errors)
- `showModal(id)` / `hideModal(id)`: Bootstrap modal helpers
- `escapeHtml(text)`: XSS prevention for dynamic DOM insertion
- `formatDate(dateString)`: formats ISO dates to `"Month DD, YYYY"` matching server-rendered output

### Pagination

The home and user-posts pages use a "Load More" pattern:
1. The server renders the first page of posts directly in the HTML
2. JavaScript tracks `currentOffset` starting after the server-rendered batch
3. Clicking "Load More" fetches `/api/posts?skip=N&limit=10` and appends rendered HTML
4. The button is hidden when `has_more` is false

### Theme Toggle

Light/Dark/Auto themes use Bootstrap's `data-bs-theme` attribute on `<html>`. The selected theme is persisted in `localStorage` and restored on every page load.

---

## Image Handling (S3)

Profile pictures are stored in AWS S3. The flow is:

1. Client uploads a file via `PATCH /api/users/{id}/picture` (multipart form)
2. Server validates size (`MAX_UPLOAD_SIZE_BYTES`, default 5 MB)
3. `process_profile_image()` in `image_utils.py`:
   - Opens the image with Pillow
   - Corrects EXIF orientation
   - Crops and resizes to exactly **300×300 px** using Lanczos resampling
   - Converts RGBA/palette modes to RGB
   - Saves as JPEG at quality 85
4. The processed bytes are uploaded to S3 at key `profile_pics/<uuid>.jpg`
5. The filename is stored in `user.image_file`
6. The old file is deleted from S3 (if one existed)

The S3 and image-processing operations run in a thread pool via `run_in_threadpool` to avoid blocking the async event loop.

The `User.image_path` property constructs the public S3 URL:
```
https://<bucket>.s3.<region>.amazonaws.com/profile_pics/<filename>
```
or falls back to `/static/profile_pics/default.jpg`.

### Verifying S3 Configuration

```bash
python check_s3.py
```

This script tests upload and delete permissions against the configured bucket.

---

## Email & Password Reset

Emails are sent via `aiosmtplib` (async SMTP). Both plain-text and HTML versions are sent in a multipart email.

The HTML template (`templates/email/password_reset.html`) is rendered with Jinja2 and contains a styled reset button plus a fallback plain-text link.

Password reset emails are dispatched as **background tasks** (FastAPI `BackgroundTasks`) so the HTTP response is returned immediately without waiting for SMTP.

Configure SMTP via environment variables (see [Configuration](#configuration)).

---

## Database & Migrations

### Engine

The app uses `create_async_engine` with `asyncpg` as the PostgreSQL driver. Sessions are managed with `async_sessionmaker` and injected via the `get_db` dependency.

### Alembic

Migrations are managed by Alembic. The `alembic/env.py` is configured for async migrations:

```bash
# Generate a migration from model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

The migration environment reads `DATABASE_URL` from the application settings (via `config.py`) rather than from `alembic.ini`, ensuring consistency with the runtime configuration.

---

## Configuration

All settings are managed by **Pydantic Settings** (`config.py`) and read from a `.env` file. Create a `.env` in the project root:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname

# JWT
SECRET_KEY=your-strong-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS S3
S3_BUCKET_NAME=your-bucket-name
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=your-access-key-id
S3_SECRET_ACCESS_KEY=your-secret-access-key
# S3_ENDPOINT_URL=  # Optional: for S3-compatible services (MinIO, LocalStack)

# Email (SMTP)
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your-smtp-username
MAIL_PASSWORD=your-smtp-password
MAIL_FROM=noreply@yourdomain.com
MAIL_USE_TLS=false

# Application
FRONTEND_URL=https://your-domain.com
POSTS_PER_PAGE=10
MAX_UPLOAD_SIZE_BYTES=5242880
RESET_TOKEN_EXPIRE_MINUTES=60
```

> **Security note:** `FRONTEND_URL` must be set explicitly — it is used to build password reset links and is intentionally **not** derived from request headers to prevent Host Header Injection.

When running on AWS ECS with an IAM role attached to the task, `S3_ACCESS_KEY_ID` and `S3_SECRET_ACCESS_KEY` can be omitted; boto3 will use the instance metadata credentials automatically.

---

## Docker & Deployment

### Multi-Stage Dockerfile

The `Dockerfile` uses a two-stage build to minimize the final image size:

1. **Builder stage** (`python:3.14-slim-bookworm`): installs build tools, creates a virtualenv, installs all Python dependencies
2. **Production stage**: copies only the virtualenv and app code, creates a non-root `appuser`, runs Uvicorn

```dockerfile
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'"]
```

`--proxy-headers` is required so that `Strict-Transport-Security` and other headers behave correctly behind the AWS load balancer / ECS. `ProxyHeadersMiddleware` is also applied in `main.py`.

### Building and Running

```bash
# Build
docker build -t fastapi-blog .

# Run locally
docker run -p 8080:8080 --env-file .env fastapi-blog
```

The container listens on `$PORT` (default `8080`).

---

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/your-username/fastapi-blog.git
cd fastapi-blog
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Copy the example and fill in your values:

```bash
cp .env.example .env
```

For local development you can use a local PostgreSQL instance and skip S3 by providing a local endpoint (e.g. MinIO or LocalStack), or use SQLite by switching the `DATABASE_URL` to an appropriate sync driver (requires code adjustment).

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Start the server

```bash
uvicorn main:app --reload
```

| URL | Description |
|---|---|
| http://127.0.0.1:8000/ | Web application |
| http://127.0.0.1:8000/docs | Swagger UI (interactive API docs) |
| http://127.0.0.1:8000/redoc | ReDoc API docs |
| http://127.0.0.1:8000/health | Health check |

---

## Testing

Tests use **pytest** with **pytest-asyncio**, **HTTPX** (`ASGITransport` for in-process requests), and **moto** to mock AWS S3.

### Test Infrastructure (`tests/conftest.py`)

- **Separate test database**: a dedicated PostgreSQL instance (default `localhost:5433/test_blog_db`)
- **Transaction rollback isolation**: each test function runs inside a transaction that is rolled back after the test, so the database starts clean for every test
- **Mocked S3**: `moto`'s `mock_aws` context manager intercepts all boto3 S3 calls
- **Dependency override**: `get_db` is overridden to inject the test session

### Running Tests

```bash
# Requires a running test PostgreSQL instance (see conftest.py for connection string)
pytest tests/

# Verbose output
pytest tests/ -v

# Run a specific file
pytest tests/test_users.py -v
```

### Test Environment Variables

The test suite sets these environment variables at import time (no `.env` file needed for tests):

```
DATABASE_URL=postgresql+asyncpg://bloguser:blogpass@localhost:5433/test_blog_db
SECRET_KEY=test-secret-key-for-testing-only
S3_BUCKET_NAME=test-bucket
S3_ACCESS_KEY_ID=testing
S3_SECRET_ACCESS_KEY=testing
S3_REGION=us-east-2
```

### Helper Functions

```python
# conftest.py exports
await create_test_user(client, username, email, password)  # Creates a user via API
await login_user(client, email, password)                  # Returns JWT token string
auth_header(token)                                         # Returns {"Authorization": "Bearer <token>"}
```

### Test Coverage

| Area | Tests |
|---|---|
| Posts — empty list | `test_get_posts_empty` |
| Posts — 404 on missing post | `test_get_post_not_found` |
| Posts — create (authenticated) | `test_create_post_success` |
| Posts — create (unauthenticated) | `test_create_post_unauthorized` |
| Posts — partial update (own post) | `test_update_post_success` |
| Posts — update (wrong user) | `test_update_post_wrong_user` |
| Posts — pagination | `test_get_posts_with_pagination` |
| Users — validation error | `test_create_user_validation_error` |
| Users — duplicate email | `test_create_user_duplicate_email` |
| Users — create success | `test_create_user_success` |
| Users — profile picture upload | `test_upload_profile_picture` |
| Users — forgot password email | `test_forgot_password_sends_email` |

---

## Security Headers

Applied to every response via an HTTP middleware in `main.py`:

```
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=63072000; includeSubDomains  (production only)
```

The `Referrer-Policy` on the reset-password page is overridden to `no-referrer` to prevent the reset token from leaking in HTTP `Referer` headers when navigating away.

---

## Health Check

```
GET /health
```

Executes `SELECT 1` against the database. Returns:

```json
{"status": "healthy"}
```

Returns `503 Service Unavailable` if the database is unreachable. Used by AWS ECS for container health monitoring.

---

<div align="center">
<p>© 2026 Adan Siqueira</p>
</div>