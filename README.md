# 📌 Assignment Task - Django REST API

A simple Django REST Framework backend built as an assignment to demonstrate:

- Authentication (JWT)
- RESTful CRUD APIs
- Celery with Redis for background email tasks

---

## 🚀 Project Overview

This project is a basic backend API built for an assignment.

It includes:

- User creation via API
- JWT authentication for login
- Celery for sending emails in background when a user is created

The goal is to demonstrate understanding of:
- Django REST Framework
- Authentication system
- CRUD APIs
- Celery background tasks

---

## 🔐 Authentication

This project uses **JWT (SimpleJWT)** for authentication.

### Features:
- User login
- Token-based authentication
- Protected APIs

---

## ⚙️ Celery Integration

Celery is used to handle **background email sending**.

### Flow:
- User is created via API
- Celery task is triggered
- Email is sent asynchronously using Redis broker

This keeps the API fast and non-blocking.

---

## 📡 API Features

### 👤 User API (CRUD)

- Create User
- Get Users
- Get Single User
- Update User
- Delete User

---

## 🔑 Auth Endpoints

| Method | Endpoint | Description |
|------|---------|-------------|
| POST | `/api/auth/login/` | Login and get JWT tokens |
| POST | `/api/auth/refresh/` | Refresh access token |

---

## 👤 User Endpoints

| Method | Endpoint | Description |
|------|---------|-------------|
| POST | `/api/users/` | Create user (triggers Celery email) |
| GET | `/api/users/` | List all users |
| GET | `/api/users/{id}/` | Retrieve user |
| PATCH | `/api/users/{id}/` | Update user |
| DELETE | `/api/users/{id}/` | Delete user |

---

## 📧 Email System (Celery)

When a user is created:

- Celery task runs in background
- Email is sent using Redis broker
- API response is returned immediately

---

## 🧰 Tech Stack

- Django 5
- Django REST Framework
- SimpleJWT
- Celery
- Redis
- SQLite

---

## ▶️ Setup Instructions

### 1. Install dependencies
```bash
pip install -r requirements.txt
```
### ▶️ Run Celery Worker

```bash
celery -A core worker -l info --pool=solo
```

## 🐳 Docker + Redis Setup

Redis is used as a message broker for Celery.

---

### 📥 1. Pull Redis Image

```bash
docker run -d --name redis-server -p 6379:6379 redis:alpine
```

### ▶️ Start Redis Container
```bash
docker start redis-server
```

### 🛑 Stop Redis Container
```bash
docker stop redis-server
```