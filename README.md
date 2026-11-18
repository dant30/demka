# DEMKA

Auto Spares & Motorbike Parts Sales System.

DEMKA is a Django and React application for inventory, sales, purchasing, and
operations, with a public preorder portal.

## Repository layout

- `backend/` - Django API and shared Python modules
- `frontend/` - React single-page application built with Vite
- `infrastructure/` - Nginx, Docker, monitoring, and operations scripts
- `ci_cd/` - CI/CD notes and supporting scripts
- `.github/workflows/` - GitHub Actions workflows
- `doc/` - Architecture, ERD, and API documentation
- `tests/` - End-to-end, integration, and performance tests

## Requirements

- Python 3.12
- Node.js 20 or newer
- PostgreSQL
- Redis for background tasks and production-like local development

## Local development

Install backend dependencies from the repository root:

```sh
python -m pip install -r backend/django/requirements/development.txt
```

Configure the PostgreSQL and Django environment variables described in
`backend/django/config/settings/base.py`. Start the API from `backend/django`:

```sh
python manage.py migrate
python manage.py runserver
```

In a second terminal, start the frontend:

```sh
cd frontend
npm ci
npm run dev
```

The Vite development server runs at `http://localhost:5173` and proxies `/api`
requests to `http://localhost:8000` by default.

## Checks

Run the backend tests from `backend/django`:

```sh
python manage.py test
```

Run frontend lint and production-build checks from `frontend`:

```sh
npm run lint
npm run build
```

GitHub Actions runs these frontend checks and the Django test suite for pushes
and pull requests. See `ci_cd/README.md` for workflow notes.