<div align="center">

# 🚗 FastAuto

**Полнофункциональная платформа для продажи автомобилей**

Объявления · Просмотры · Бронирование · Сделки · Тикеты · AI-ассистент

[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=white)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io)

</div>

---

## ✨ Возможности

| Модуль | Описание |
|--------|----------|
| 🗂 **Каталог** | Поиск и фильтрация авто по марке, модели, поколению, цене, пробегу, типу кузова и КПП |
| 📋 **Объявления** | Создание, редактирование и публикация с фото, VIN, адресом и условиями оплаты |
| 📅 **Просмотры** | Запись на осмотр авто в удобное время через встроенный планировщик |
| 🔒 **Бронирование** | Резервация с депозитом через YooKassa (двухстадийный холд) |
| 🤖 **AI-ассистент** | Умный помощник на базе Ollama для подбора и консультации |
| 💬 **Тикеты** | Система обращений: создание, назначение, переписка |
| ❤️ **Избранное** | Сохранение понравившихся объявлений |
| 🛡 **Админ-панель** | Управление объявлениями, пользователями, брониями, модерация и статистика |
| 🌐 **i18n** | Полная локализация RU / EN |

---

## 🏗 Архитектура

```
FastAuto/
├── frontend/                  # React SPA (TypeScript + Vite)
│   └── src/app/
│       ├── pages/             # страницы приложения
│       ├── components/        # UI-компоненты
│       ├── api/               # клиенты для backend API
│       ├── hooks/             # React-хуки
│       └── i18n/              # переводы RU / EN
│
├── backend/                   # FastAPI backend
│   ├── app/
│   │   ├── api/routes/        # HTTP-эндпоинты
│   │   ├── models/            # SQLModel-модели (БД)
│   │   ├── schemas/           # Pydantic-схемы
│   │   ├── crud/              # слой работы с БД
│   │   ├── services/          # бизнес-логика
│   │   └── core/              # конфиг, безопасность, кэш
│   ├── alembic/               # миграции БД
│   └── tests/                 # unit + integration тесты
│
├── docker-compose.yml         # production: всё одной командой
└── .env.example               # шаблон переменных окружения
```

---

## 🛠 Технологический стек

### Frontend

| Технология | Версия | Назначение |
|-----------|--------|------------|
| React | 19 | UI-фреймворк |
| TypeScript | 5 | Типизация |
| Vite | 6 | Сборщик |
| Tailwind CSS | v4 | Стили |
| Radix UI | latest | Компоненты |
| React Router | v7 | Маршрутизация |
| Sonner | latest | Уведомления |
| Lucide React | latest | Иконки |

### Backend

| Технология | Версия | Назначение |
|-----------|--------|------------|
| Python | 3.12 | Язык |
| FastAPI | 0.115 | Web-фреймворк |
| SQLModel | 0.0.22 | ORM |
| Granian | 2.7 | ASGI-сервер |
| Alembic | 1.14 | Миграции БД |
| Pydantic | 2 | Валидация данных |
| PyJWT + Argon2 | latest | Аутентификация |
| APScheduler | 3.11 | Фоновые задачи |
| Ollama | 0.4 | AI-интеграция |
| YooKassa | 3.10 | Платежи |

### Инфраструктура

| Сервис | Назначение |
|--------|------------|
| PostgreSQL 17 | Основная база данных |
| Redis 7 | Кэш + rate limiting |
| MinIO | Хранилище файлов (S3-совместимое) |
| nginx | Reverse proxy + brotli-сжатие |

---

## 🚀 Быстрый старт (Production)

> Протестировано на VPS с **4 GB RAM / 30 GB диска**.

### 1. Клонировать репозиторий

```bash
git clone https://github.com/CHUVISS/FastAuto /home/user1alex/app
cd /home/user1alex/app
```

### 2. Настроить окружение

```bash
cp .env.example .env
nano .env
```

Ключевые переменные:

| Переменная | Как заполнить |
|-----------|---------------|
| `SECRET_KEY` / `REFRESH_SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `POSTGRES_PASSWORD` | надёжный случайный пароль |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | ключи MinIO |
| `MINIO_PUBLIC_URL` | `http://<IP-сервера>/minio` |
| `BACKEND_CORS_ORIGINS` | `"http://<IP-сервера>"` |
| `FRONTEND_BASE_URL` | `http://<IP-сервера>` |
| `FIRST_SUPERUSER_EMAIL` / `_PASSWORD` | данные первого администратора |

### 3. Собрать и запустить

```bash
docker compose up -d --build
```

Одна команда запускает всё:

- ✅ Сборку React-фронтенда (Node.js внутри Docker, на сервере не нужен)
- ✅ Сборку Python-бэкенда
- ✅ PostgreSQL, Redis, MinIO, бэкенд (2 воркера), nginx на порту **80**
- ✅ Автоматические миграции БД и заполнение справочников

### 4. Проверить

```bash
docker compose ps
curl http://localhost/api/v1/health
```

Открыть в браузере: `http://<IP-сервера>`

---

## 💻 Локальная разработка

### Требования

- Docker + Docker Compose v2
- Node.js 22+

### Бэкенд + инфраструктура

```bash
cd backend
docker compose up -d
```

| Адрес | Что открывается |
|-------|----------------|
| `http://localhost/api/v1` | REST API |
| `http://localhost/api/v1/docs` | Swagger UI |

### Фронтенд (dev-сервер с hot-reload)

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

### AI-ассистент (опционально)

```bash
cd backend
docker compose --profile docker-ai up -d
```

> Требует ~4 GB свободной RAM для модели по умолчанию.

---

## 🔄 Обновление на сервере

```bash
cd /home/user1alex/app
git pull origin main
docker compose up -d --build
```

---

## 🧪 Тесты

```bash
# Backend
cd backend
docker compose up -d db redis
uv run pytest

# Frontend
cd frontend
npm run test:run

# С отчётом о покрытии
npm run test:coverage
```

---

## 📊 Потребление ресурсов (4 GB VPS)

| Сервис | RAM |
|--------|-----|
| PostgreSQL | ~700 MB |
| Redis | ~300 MB |
| MinIO | ~150 MB |
| Backend (2 воркера) | ~400 MB |
| nginx | ~50 MB |
| **Итого** | **~1.6 GB** |

---

## 🗺 Маршрутизация nginx

| Путь | Обработчик |
|------|-----------|
| `/` | React SPA (статические файлы) |
| `/api/v1/listings*` | Бэкенд (кэш nginx 10 мин) |
| `/api/*` | Бэкенд (без кэша) |
| `/minio/*` | MinIO (медиафайлы) |

---

<div align="center">

Сделано с ❤️ — FastAPI + React

</div>
