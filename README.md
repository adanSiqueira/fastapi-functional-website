<div align="center">

# FastAPI App Blueprint

<br/>

![Python](https://img.shields.io/badge/Python-3.13+-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red?style=for-the-badge&logo=databricks&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Jinja](https://img.shields.io/badge/Jinja2-Templates-black?style=for-the-badge&logo=jinja&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-Frontend-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
</div>


A blog application built with **FastAPI**, featuring both:

* a **REST API** (`/api/...`) for programmatic access
* a **server-rendered website** using **Jinja2 templates**

This project is a application built not only as a functional website, but also as a reusable blueprint for any system that requires similar core behavior — such as user accounts, login/logout flows, post creation, chronological content organization, and full CRUD operations.

While the business logic could easily be adapted to other domains (news platforms, forums, social feeds, product reviews, etc.), the underlying architecture is designed to be stable, clean, and scalable. 

Authentication and authorization are currently under development to fully secure routes and user actions.

This project take the following principles as its building concerns:

* async FastAPI architecture
* modular routers design
* clean separation of concerns
* SQLAlchemy ORM relationships
* template rendering + static file serving
* proper exception handling for both API + frontend
* production-style project layout

---

##  Features

### ✅ Web Application (Jinja2 + Bootstrap UI)

* Homepage displaying all posts (latest first)
* Single post page (`/posts/{id}`)
* User posts page (`/users/{id}/posts`)
* Bootstrap layout with responsive design
* Bootstrap modals for:

  * Creating new posts
  * Editing posts
  * Deleting posts
* Light/Dark/Auto theme toggle
* Profile picture support (default image if missing)
* Custom error page rendering for web routes

---

### ✅ REST API (FastAPI JSON Endpoints)

#### Users API (`/api/users`)

* Create user
* Get a user by ID
* List all users
* Get all posts of a user
* Update user partially (PATCH)
* Delete user

#### Posts API (`/api/posts`)

* List all posts (ordered by most recent)
* Get post by ID
* Create post
* Full update (PUT)
* Partial update (PATCH)
* Delete post

All endpoints use **Pydantic schemas** for validation and response formatting.

---

### ✅ Database Layer

* Async SQLAlchemy ORM models (`User`, `Post`)
* SQLite database (`blog.db`)
* Automatic table creation at app startup via FastAPI lifespan
* Proper relationships:

  * One User → Many Posts
  * Each Post belongs to a User

---

### ✅ Error Handling

This project uses **custom exception handlers** to provide different behavior for:

* API requests (`/api/...`) → returns JSON responses (default FastAPI style)
* Website requests → renders `error.html` template with friendly UI

Handled errors include:

* Standard HTTP errors (404, 400, etc.)
* Validation errors (422)

---

## 🛠️ Tech Stack

### Backend

* **Python 3.13+**
* **FastAPI**
* **SQLAlchemy (Async ORM)**
* **Pydantic**
* **Uvicorn**

### Frontend

* **Jinja2 Templates**
* **Bootstrap 5**
* Vanilla JavaScript (Fetch API + Modules)

### Database

* **SQLite**

### Static Files

* Custom CSS
* Icons + manifest (PWA-ready)
* Default profile picture
* Media folder for user profile images

---

## 📂 Project Structure

```bash
.
├── main.py                  # FastAPI app entrypoint + webpage routes
├── database.py              # Database engine + async session dependency
├── models.py                # SQLAlchemy ORM models
├── schemas.py               # Pydantic schemas for validation/serialization
├── routers/
│   ├── posts.py             # Posts API endpoints
│   ├── users.py             # Users API endpoints
│   └── __init__.py
├── templates/               # Jinja2 HTML templates
│   ├── layout.html
│   ├── home.html
│   ├── post.html
│   ├── user_posts.html
│   └── error.html
├── static/                  # Static assets (css, js, icons)
│   ├── css/
│   ├── js/
│   ├── icons/
│   └── profile_pics/
├── media/
│   └── profile_pics/        # Uploaded profile images (future use)
├── blog.db                  # SQLite database
├── requirements.txt         # Dependencies list
├── pyproject.toml           # Project metadata
└── README.md
```

---

##  Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Create and activate a virtual environment

#### Windows (PowerShell)

```powershell
python -m venv venv
venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Project

Start the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload
```

Now open:

* Web App: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**
* Swagger Docs: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
* ReDoc Docs: **[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)**

---

##  Web Routes

| Route                    | Description                     |
| ------------------------ | ------------------------------- |
| `/`                      | Home page (all posts)           |
| `/posts/{post_id}`       | View a single post              |
| `/users/{user_id}/posts` | View posts from a specific user |

---

##  API Routes

### Users (`/api/users`)

| Method | Endpoint                     | Description      |
| ------ | ---------------------------- | ---------------- |
| POST   | `/api/users`                 | Create user      |
| GET    | `/api/users`                 | List users       |
| GET    | `/api/users/{user_id}`       | Get user         |
| GET    | `/api/users/{user_id}/posts` | Get user's posts |
| PATCH  | `/api/users/{user_id}`       | Update user      |
| DELETE | `/api/users/{user_id}`       | Delete user      |

---

### Posts (`/api/posts`)

| Method | Endpoint               | Description    |
| ------ | ---------------------- | -------------- |
| GET    | `/api/posts`           | List posts     |
| POST   | `/api/posts`           | Create post    |
| GET    | `/api/posts/{post_id}` | Get post       |
| PUT    | `/api/posts/{post_id}` | Full update    |
| PATCH  | `/api/posts/{post_id}` | Partial update |
| DELETE | `/api/posts/{post_id}` | Delete post    |

---

##  Example API Requests

### Create a User

```bash
curl -X POST http://127.0.0.1:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "adan",
    "email": "adan@email.com"
  }'
```

### Create a Post

```bash
curl -X POST http://127.0.0.1:8000/api/posts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "content": "This is my first blog post!",
    "user_id": 1
  }'
```

---

##  Profile Pictures

Users support an optional `image_file` field.

* If the user has an uploaded profile image, the project serves it from:

```
/media/profile_pics/<filename>
```

* If not, it automatically falls back to:

```
/static/profile_pics/default.jpg
```

This logic is implemented in the `User.image_path` property inside `models.py`.

---

##  Current Limitations / TODO

This project is currently in early development and still lacks authentication.

Planned future improvements:

* [ ] Authentication system (JWT or session cookies)
* [ ] Register/Login UI integration
* [ ] Restrict post creation/edit/delete to authenticated users
* [ ] File upload support for profile pictures
* [ ] Pagination on posts list
* [ ] Search and filtering
* [ ] Deployment setup (Docker + Render/Fly.io)

---

##  Notes About Current Implementation

### Temporary Authorization Behavior

In the templates, post actions are temporarily hardcoded to user ID `3`.

Example:

* New post form automatically sets:

```js
postData.user_id = 3;
```

And post edit/delete buttons are only shown if:

```jinja2
{% if post.user_id == 3 %}
```

This will be replaced once authentication is implemented.


