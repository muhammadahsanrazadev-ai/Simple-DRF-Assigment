# Task Manager API

A Django REST Framework backend for managing tasks with **JWT authentication**,
**role-based permissions**, and **Celery + Redis** powered background email
notifications (task assignment, completion, and priority-based due-date
reminders).

Built as a backend assignment to demonstrate: DRF, JWT auth, Celery, and
clean CRUD API design.

---

## 1. Core Concept

Two roles, no extra "role" field — just Django's built-in `is_superuser` flag:

| Role | Can do |
|---|---|
| **Superuser (Admin)** | Create/deactivate users. Create tasks and assign them to a user. See and manage **every** task in the system. |
| **Regular user** | See only tasks assigned to them. Change a task's status from `pending` to `completed` — nothing else. |

**Why Celery?** Sending email is slow, I/O-bound work. If it ran inline inside
a request, the API response would block on an SMTP round-trip. Instead, the
view enqueues a message into **Redis** (the broker) and returns immediately;
a separate **Celery worker** process picks the message up and sends the email
in the background. A second process, **Celery Beat**, runs one scheduled job
every hour that scans the `Task` table and sends due-date reminders or
overdue notices — no per-task scheduling needed, so deleting or reassigning
a task "just works" without any manual cleanup.

### Email matrix

| Event | Email goes to |
|---|---|
| Superuser creates a user | The new user (welcome email) |
| Superuser deactivates a user | That user (account deactivated + tasks unassigned) |
| Superuser creates/assigns a task | The assigned user (new task assigned) |
| User marks their task `completed` | The superuser who created the task |
| Task becomes overdue (periodic check) | Both the assigned user and the creator |
| HIGH priority task, 24h before due | The assigned user |
| HIGH priority task, 1h before due | The assigned user (2nd reminder) |
| LOW priority task | No upcoming reminder — only the one-time overdue notice above |

### Soft-delete

"Deleting" a user never removes the database row. It sets `is_active=False`
(Django's auth backend then refuses to log that user in), unassigns every
task they had (`assigned_to` becomes `NULL`), and sends them a final
notification — all while preserving the row, the email address, and
historical task records.

---

## 2. Tech Stack

- Django 5 + Django REST Framework
- SimpleJWT (access + refresh tokens)
- Celery 5 + Redis (broker and result backend)
- Celery Beat (`django-celery-beat`, DB-backed schedule)
- SQLite (zero extra setup)
- `python-decouple` for `.env`-based configuration
- `django-filter` for query filtering

---

## 3. Project Structure

```
task_manager/
├── config/              # project settings, urls, celery app
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── celery_utils.py  # safe_enqueue() helper, see Design Notes below
├── users/                # custom User model, superuser-only user management
│   ├── models.py
│   ├── serializers.py
│   ├── permissions.py
│   ├── views.py
│   ├── tasks.py          # Celery tasks: welcome email, deactivation email
│   └── urls.py
├── tasks/                 # Task model + CRUD API + reminder logic
│   ├── models.py
│   ├── serializers.py
│   ├── permissions.py
│   ├── views.py
│   ├── tasks.py           # Celery tasks: assigned/completed/overdue emails
│   │                      # + the hourly periodic reminder job
│   ├── urls.py
│   └── management/commands/setup_periodic_tasks.py
├── .env                   # your real local secrets (git-ignored)
├── .env.example           # template — copy this to .env
└── requirements.txt
```

---

## 4. Setup (Windows, using venv + Docker Desktop for Redis)

### 4.1 Clone and create a virtual environment

```powershell
cd task_manager
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4.2 Configure environment variables

```powershell
copy .env.example .env
```

Open `.env` and fill in:
- `SECRET_KEY` — generate one with:
  ```powershell
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- JWT token lifetimes (`JWT_ACCESS_TOKEN_LIFETIME_MINUTES`,
  `JWT_REFRESH_TOKEN_LIFETIME_MINUTES`) — the defaults are fine for testing
  (60 minutes / 7 days).
- Email: leave `EMAIL_BACKEND` on the console backend to just print emails
  to your terminal — no real credentials needed. Switch to the SMTP backend
  plus a Gmail App Password if you want real emails sent.

### 4.3 Start Redis (Docker Desktop)

```powershell
docker run -d --name redis-server -p 6379:6379 redis:alpine
```

Already created it before? Just start it again:
```powershell
docker start redis-server
```

Verify it's up:
```powershell
docker exec -it redis-server redis-cli ping
```
Expected output: `PONG`

### 4.4 Run migrations and create a superuser

```powershell
python manage.py migrate
python manage.py createsuperuser
```

### 4.5 Register the periodic reminder schedule (run once)

```powershell
python manage.py setup_periodic_tasks
```

### 4.6 Run everything — 3 separate terminals, all with venv activated

```powershell
# Terminal 1 - Django API
python manage.py runserver

# Terminal 2 - Celery worker (sends the actual emails)
celery -A config worker -l info --pool=solo

# Terminal 3 - Celery Beat (fires the hourly reminder job)
celery -A config beat -l info
```

Note: `--pool=solo` is needed for the worker on Windows, since Celery's
default worker pool relies on `fork()`, which Windows doesn't support.

---

## 5. API Reference

All endpoints are prefixed with `/api/`. Every endpoint except login/refresh
requires the header: `Authorization: Bearer <access_token>`.

### Auth

| Method | Endpoint | Body | Description |
|---|---|---|---|
| POST | `/api/auth/login/` | `username, password` | Returns `access` and `refresh` tokens |
| POST | `/api/auth/refresh/` | `refresh` | Returns a new `access` token |

### Users (superuser only)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/users/` | List all users |
| POST | `/api/users/` | Create a user, sends a welcome email |
| GET | `/api/users/{id}/` | Retrieve a user |
| PATCH | `/api/users/{id}/` | Update a user |
| DELETE | `/api/users/{id}/` | Soft-delete: deactivate, unassign their tasks, send email |

### Tasks

| Method | Endpoint | Who | Description |
|---|---|---|---|
| GET | `/api/tasks/` | Both | List tasks (superuser sees all; user sees only their own) |
| POST | `/api/tasks/` | Superuser only | Create a task, optionally with `assigned_to_id`, sends an "assigned" email |
| GET | `/api/tasks/{id}/` | Both | Retrieve a single task |
| PATCH | `/api/tasks/{id}/` | Both | Superuser: any field. Regular user: only `status` to `"completed"` |
| DELETE | `/api/tasks/{id}/` | Superuser only | Delete a task |

Query params on the list endpoint: `status=pending`, `priority=HIGH`,
`search=report`, `ordering=-due_date`.

### Example flow

```powershell
# 1. Login as superuser
curl -X POST http://127.0.0.1:8000/api/auth/login/ -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"yourpassword\"}"

# 2. Create a user (use the access token from step 1)
curl -X POST http://127.0.0.1:8000/api/users/ -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d "{\"username\":\"ahsan\",\"email\":\"ahsan@example.com\",\"password\":\"SomePass123!\"}"

# 3. Create a task assigned to that user
curl -X POST http://127.0.0.1:8000/api/tasks/ -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d "{\"title\":\"Finish report\",\"due_date\":\"2026-07-01T10:00:00Z\",\"priority\":\"HIGH\",\"assigned_to_id\":2}"
```

---

## 6. Design notes (decisions worth being able to explain)

- **Periodic query job instead of per-task scheduling.** Reminders come from
  one Celery Beat job that re-queries the `Task` table every hour, rather
  than scheduling an individual job per task with `apply_async(eta=...)`.
  This means deleting or reassigning a task needs no manual revoke call —
  a deleted task simply stops appearing in the next query.
- **Boolean flags for idempotency.** `reminder_24h_sent`, `reminder_1h_sent`,
  and `overdue_notified` exist purely so re-running the same hourly query
  doesn't re-send an email that already went out. Marking a task completed
  force-sets the reminder flags to `True`, which is what silences all
  further reminders for it.
- **`safe_enqueue()` in `config/celery_utils.py`.** A bare `.delay()` call
  talks to Redis synchronously; if the broker is down, that exception would
  otherwise bubble up and turn a successful database write into a 500
  error. `safe_enqueue()` catches that specific failure and logs it instead
  — the core CRUD operation never depends on the notification system being
  up.
- **Soft-delete via `is_active`, not `.delete()`.** Keeps the email address
  and historical task records around, and Django's auth backend already
  refuses to authenticate inactive users for free.
- **Two separate owner fields** (`assigned_to`, `created_by`) instead of
  one, since the assigned user and the responsible superuser receive
  different notifications for different events.
