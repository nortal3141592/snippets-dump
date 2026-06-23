# snippets-dump

A personal notes and snippets web application built from scratch as a backend engineering learning project. Write notes, organise them with tags, and find them instantly with tag filtering.

> **Disclaimer:** The backend was entirely designed and written by hand but every architectural decision, data model, API endpoint, and piece of business logic was thought through and implemented manually. The frontend was vibe coded using AI generation tools.

---

## What I built and what I learned

This project was not about finishing fast. It was about learning how experienced backend engineers think and make decisions. Along the way I worked through:

- **Authentication and authorisation** --> JWT-based auth with `PyJWT`, password hashing with `pwdlib`, and a `CurrentUser` dependency that validates every protected request
- **Many-to-many relationships** --> Notes and tags connected through a junction table, designed from scratch including the reasoning behind why a junction table exists
- **Smart tag management** --> A "get or create" pattern that reuses existing tags, orphan cleanup that deletes tags when no notes reference them anymore, and per-user tag isolation enforced at the database level
- **Tag filtering** --> `GET /api/notes?tag=python` using SQLAlchemy's `.any()` to filter at the database level, not in Python memory
- **Rate limiting** --> Request limiting on sensitive endpoints using `slowapi` middleware
- **Async throughout** --> Every endpoint and database operation is fully async using SQLAlchemy's async engine with `aiosqlite`
- **API design** --> Deliberate decisions about REST structure, HTTP status codes, ownership enforcement, and what to expose vs protect
- **Project organisation** --> Layered structure with routers, schemas, models, auth, config, and database concerns separated into their own files

---

## Tech stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | SQLite via aiosqlite |
| ORM | SQLAlchemy (async) |
| Auth | JWT (PyJWT) + pwdlib |
| Validation | Pydantic v2 |
| Rate limiting | slowapi |
| Templates | Jinja2 |
| Package manager | uv |
| Python | 3.12 |

---

## Project structure

```
snippets-dump/
├── main.py              # App entry point, lifespan, middleware, routes
├── database.py          # Async engine and session setup
├── models.py            # SQLAlchemy models (User, Note, Tag, junction table)
├── schemas.py           # Pydantic request/response schemas
├── auth.py              # JWT creation, verification, CurrentUser dependency
├── limiter.py           # Rate limiter instance (shared across routers)
├── config.py            # Settings loaded from .env
├── routers/
│   ├── users.py         # User CRUD + login endpoints
│   └── notes.py         # Note CRUD + tag management endpoints
├── Templates/           # Jinja2 HTML templates (vibe-coded frontend)
│   ├── layout.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── create.html
│   ├── note.html
│   ├── profile.html
│   └── error.html
├── static/              # CSS, JS, profile pictures
├── media/               # Uploaded media files
├── pyproject.toml
└── .env                 # Secret keys and config (not committed)
```

---

## API endpoints

### Users — `/api/users`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/users` | No | Create account |
| POST | `/api/users/token` | No | Login, get JWT |
| GET | `/api/users/me` | Yes | Get your profile |
| PATCH | `/api/users/{user_id}` | Yes | Update your profile |
| DELETE | `/api/users/{user_id}` | Yes | Delete your account |

### Notes — `/api/notes`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/notes` | Yes | Get all your notes |
| GET | `/api/notes?tag=python` | Yes | Filter notes by tag |
| POST | `/api/notes` | Yes | Create a note |
| GET | `/api/notes/{note_id}` | Yes | Get a single note |
| PATCH | `/api/notes/{note_id}` | Yes | Update heading or body |
| DELETE | `/api/notes/{note_id}` | Yes | Delete a note |
| POST | `/api/notes/{note_id}/tags` | Yes | Add a tag to a note |
| DELETE | `/api/notes/{note_id}/tags/{tag_id}` | Yes | Remove a tag from a note |

---

## Running this locally

These instructions are written to be beginner-friendly. Follow them step by step.

### Prerequisites

- Python 3.12 installed on your machine
- `uv` installed — if you don't have it: `pip install uv`
- Git installed

### Step 1 — Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/snippets-dump.git
cd snippets-dump
```

### Step 2 — Set the Python version

```bash
echo "3.12" > .python-version
```

### Step 3 — Create a virtual environment

```bash
uv venv --python 3.12
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
```

### Step 4 — Install dependencies

```bash
uv pip install fastapi uvicorn sqlalchemy aiosqlite 'pydantic[email]' python-jose pwdlib slowapi jinja2 python-multipart
```

### Step 5 — Set up your environment file

Create a `.env` file in the root of the project:

```
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

To generate a secure secret key, run this in your terminal:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste it as your `SECRET_KEY`.

### Step 6 — Run the server

```bash
uvicorn main:app --reload
```

The app will be available at `http://127.0.0.1:8000`

### Step 7 — Explore the API

Visit `http://127.0.0.1:8000/docs` for the interactive API documentation where you can test every endpoint directly in the browser.

---

## Notes on design decisions

A few deliberate choices worth knowing about:

**Tags are per-user.** Two users can both have a tag called "python", they are completely separate records. Tag ownership is enforced at the database level with a unique constraint on `(tagname, user_id)`.

**Orphan tag cleanup.** When you remove a tag from a note, the application checks whether that tag is still attached to any other notes. If not, the tag is deleted from the database automatically. Same happens when a note is deleted.

**Authorization by ownership.** Every note and tag operation verifies that the resource belongs to the currently authenticated user before doing anything. A user can never read, modify, or delete another user's data.

**Single commit per request.** Database operations within a single request are batched and committed once at the end, keeping transactions clean and consistent.

---

## Known limitations

This is a learning project, not a production service. Some things intentionally left simple:

- SQLite is used for simplicity - a production deployment would use PostgreSQL
- No automated tests - manual testing only
- No token refresh mechanism - expired tokens require re-login
- Rate limiting is IP-based and stored in memory - resets on server restart
- No pagination on note listing

---

## About the project
This project was created as a backend engineering learning project.

The primary goal was not to build the most feature-rich notes application, but to understand how modern backend systems are designed and implemented from scratch. Every database relationship, API endpoint, authentication flow, authorization check, and architectural decision was intentionally written and reasoned through as part of the learning process.

While the application is fully usable as a personal notes app, it was never intended to be a production-ready or enterprise-grade service. Simplicity was often chosen over scalability so that the underlying concepts remained easy to understand and explore.

If this project helps another student understand backend development, then it has already achieved more than its original purpose.

## A personal note
We live in a time where AI can generate entire applications, from frontend interfaces to backend APIs, database models, authentication systems, deployment pipelines, and even documentation.

That's an incredible tool, but I still believe there's value in understanding **why** these pieces exist before relying on automation to build them.

This project was my way of learning the fundamentals: how authentication works, why authorization matters, how databases are modeled, how APIs are designed, how HTTP requests flow through an application, how ORMs translate Python into SQL, and how different layers of a backend interact.

I don't think writing everything manually makes someone a better engineer forever,**but** I do think understanding the fundamentals makes AI a much more powerful tool rather than a crutch.

This repository is one small step in that learning journey, and I hope it encourages others to build things from first principles before letting AI accelerate the process.