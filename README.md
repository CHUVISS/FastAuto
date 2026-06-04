# Car Sales

A full-stack platform for car sales workflow: listings, viewings, reservations, deals, messaging, and an AI assistant.

## Structure

```
.
├── frontend/              # React SPA
├── backend/               # FastAPI backend + Docker configs
│   ├── app/               # Python source
│   ├── nginx/             # nginx configs
│   ├── scripts/           # startup + seed scripts
│   ├── Dockerfile         # backend image
│   └── Dockerfile.nginx   # nginx image (builds frontend inside)
├── docker-compose.yml     # production: one command to run everything
└── .env.example           # environment template
```

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4, Radix UI, React Router v7 |
| Backend | Python 3.12, FastAPI, SQLModel, Granian (ASGI) |
| Database | PostgreSQL 17 |
| Cache | Redis 7 |
| File storage | MinIO (S3-compatible) |
| Reverse proxy | nginx with brotli compression |
| AI assistant | Ollama (optional, requires separate server) |

## Production deployment

Tested on a **4 GB RAM / 30 GB disk** VPS.

### 1. Clone the repository

```bash
git clone <repo-url> /srv/app
cd /srv/app
```

### 2. Configure environment

```bash
cp .env.example .env
nano .env          # fill in every CHANGEME value
```

Key variables:

| Variable | What to set |
|---|---|
| `SECRET_KEY` / `REFRESH_SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `POSTGRES_PASSWORD` | strong random password |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | MinIO credentials |
| `MINIO_PUBLIC_URL` | `http://<your-server-ip>/minio` |
| `BACKEND_CORS_ORIGINS` | `"http://<your-server-ip>"` |
| `FRONTEND_BASE_URL` | `http://<your-server-ip>` |
| `FIRST_SUPERUSER_EMAIL` / `_PASSWORD` | initial admin account |

### 3. Build and start

```bash
docker compose up -d --build
```

This single command:
- Builds the React frontend (Node.js inside Docker, no Node needed on the server)
- Builds the Python backend
- Starts PostgreSQL, Redis, MinIO, backend (2 workers), nginx on port 80
- Runs database migrations and seeds reference data automatically

### 4. Verify

```bash
docker compose ps
curl http://localhost/api/v1/health
```

Open `http://<your-server-ip>` in a browser.

### Routing

| Path | Served by |
|---|---|
| `/` | React SPA (static files from nginx) |
| `/api/v1/cars*` | Backend (nginx-cached, 10 min) |
| `/api/*` | Backend (no cache) |
| `/minio/*` | MinIO file storage |

### Resource usage (4 GB server)

| Service | RAM |
|---|---|
| PostgreSQL | ~700 MB |
| Redis | ~300 MB |
| MinIO | ~150 MB |
| Backend (2 workers) | ~400 MB |
| nginx | ~50 MB |
| **Total** | **~1.6 GB** |

### Update after code changes

```bash
git pull
docker compose up -d --build
```

---

## Local development

### Prerequisites

- Docker + Docker Compose v2
- Node.js 22+ (for frontend hot-reload)

### Backend + infrastructure

```bash
cd backend

cp .env.example .env          # adjust values if needed

docker compose up -d          # uses compose.yml + compose.override.yml automatically
```

API: `http://localhost/api/v1` — Docs: `http://localhost/api/v1/docs`

### Frontend (dev server)

```bash
cd frontend

npm install
npm run dev                   # http://localhost:5173
```

### Optional: AI assistant (Ollama)

```bash
cd backend
docker compose --profile docker-ai up -d
```

Requires ~4 GB of free RAM for the default model.

---

## Running tests

```bash
# Backend
cd backend
docker compose up -d db redis
uv run pytest

# Frontend
cd frontend
npm run test:run
```
