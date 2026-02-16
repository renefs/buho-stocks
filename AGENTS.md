# AI Agents Guide - Buho Stocks

This document provides essential information for AI agents working on the Buho Stocks codebase.

## Project Overview

Buho Stocks is a portfolio management application for tracking stocks, dividends, and returns using a Buy & Hold investment strategy. It consists of a Django REST API backend and a React frontend.

## Project Structure

```
buho-stocks/
├── backend/                 # Django REST API
│   ├── buho_backend/       # Main Django app (settings, urls, celery, websockets)
│   ├── companies/          # Company management
│   ├── currencies/         # Currency handling
│   ├── dividends_transactions/  # Dividend tracking
│   ├── exchange_rates/     # Currency exchange rates
│   ├── markets/            # Stock markets
│   ├── portfolios/         # Portfolio management
│   ├── rights_transactions/ # Rights transactions
│   ├── sectors/            # Stock sectors
│   ├── settings/           # User settings
│   ├── shares_transactions/ # Share buy/sell transactions
│   ├── stats/              # Statistics calculations
│   ├── stock_prices/       # Stock price fetching
│   └── benchmarks/         # Benchmark comparisons
├── client/                  # React frontend (Vite + TypeScript)
│   ├── src/                # Source code
│   └── tests/              # Playwright E2E tests
├── data/                    # SQLite database (development)
├── docs/                    # Documentation
└── docker-compose.yml       # Production Docker setup
```

## Technology Stack

### Backend

- **Python 3.11** (required)
- **Django 5** with Django REST Framework
- **Celery** for background tasks
- **Channels** for WebSocket support
- **uv** for dependency management (not pip)
- **Database**: SQLite (dev), MariaDB (prod)
- **Cache/Broker**: Redis

### Frontend

- **Node.js 20** (required)
- **React 18** with TypeScript
- **Vite** for build tooling
- **Mantine UI 7** component library
- **TanStack Query** for data fetching
- **Vitest** for unit testing

## Development Environment Setup

### Prerequisites

1. Python 3.11
2. Node.js 20
3. Redis (for Celery/WebSockets)
4. uv (Python package manager)

### Backend Setup

```bash
# Copy environment file
cp .env.sample .env
# Edit .env and configure paths

# Install dependencies with uv
uv sync --all-extras

# Run migrations
cd backend && uv run python manage.py migrate

# Start development server
uv run python manage.py runserver
```

### Frontend Setup

```bash
cd client
npm install
npm start
```

### Environment Variables

Copy `.env.sample` to `.env` and configure:

- `DATABASE_SQLITE_PATH`: Path to SQLite database
- `MEDIA_ROOT`: Path for uploaded files
- `SECRET_KEY`: Django secret key
- `REDIS_HOSTNAME`: Redis server (default: localhost for dev)
- `TIME_ZONE`: Application timezone

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
uv run python manage.py test

# Run with coverage
uv run coverage run manage.py test
uv run coverage report
uv run coverage xml

# Run specific app tests
uv run python manage.py test companies
uv run python manage.py test portfolios.tests.test_views

# Run tests matching a pattern
uv run python manage.py test --pattern="test_*.py"
```

**Test Configuration**: Uses `pytest-django` with settings in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "buho_backend.settings"
python_files = ["tests.py", "test_*.py", "*_tests.py"]
```

### Frontend Tests

```bash
cd client

# Run all tests
npm run test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run coverage
```

**Test Configuration**: Vitest with jsdom environment, setup in `vite.config.mjs`.

## Code Style Guidelines

### Python (Backend)

- **Formatter & Linter**: Ruff (replaces black, isort, flake8)
- **Type Checking**: mypy with django-stubs

```bash
# Format code
uv run ruff format backend/

# Lint and auto-fix
uv run ruff check backend/ --fix

# Lint only (no fix)
uv run ruff check backend/

# Type check
uv run mypy backend/

# Security scan
uv run bandit -r backend/
```

### TypeScript/React (Frontend)

- **Formatter & Linter**: Biome (replaces ESLint and Prettier)
- **Import Organization**: Handled by Biome

```bash
cd client

# Lint
npm run lint

# Lint and auto-fix
npm run lint:fix

# Format
npm run format

# Check formatting
npm run format:check

# Both lint and format (recommended)
npm run check:fix
```

### Pre-commit Hooks

The project uses pre-commit for automated checks:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

Configured hooks: ruff (lint + format), bandit

## API Conventions

### REST API

- Base URL: `/api/v1/`
- Uses **camelCase** for JSON keys (automatic conversion via djangorestframework-camel-case)
- API documentation available at `/swagger/` (drf-yasg)

### Response Format

Backend uses snake_case internally; API responses are automatically converted to camelCase for the frontend.

## Pull Request Guidelines

1. **Branch from `develop`** (git-flow workflow)
2. **Discuss changes first** via GitHub Issues for non-trivial changes
3. **One feature per PR** - don't mix unrelated changes
4. **Squash commits** if there was churn during development
5. **Separate refactoring** from feature changes when possible

### Commit Message Format

- Subject: 50 chars max, imperative mood, capitalized, no period
- Body: 72 char wrap, explain what and why

### PR Checklist

- [ ] Tests pass (`uv run python manage.py test` and `npm test`)
- [ ] Code is formatted (`ruff format`, `biome format`)
- [ ] Linting passes (`ruff check`, `biome lint`)
- [ ] Type checking passes (mypy)
- [ ] New features include tests
- [ ] Documentation updated if needed

## CI/CD Pipeline

GitHub Actions workflows:

- **Django CI** (`django.yml`): Python tests + coverage → Codecov
- **React CI** (`react.yml`): Lint + tests + coverage → Codecov
- **Docker builds**: Automatic image publishing on tags

CI runs on pushes and PRs to `main` and `develop` branches.

## Security Considerations

### Backend

- **bandit** runs in pre-commit for security scanning
- Never commit secrets or API keys
- Use `python-decouple` for environment variables
- Sentry integration available (configure `SENTRY_DSN`)

### Frontend

- No inline scripts or styles
- Use environment variables for API URLs (`VITE_API_URL`)
- Validate all user inputs

### Sensitive Files

Never commit:

- `.env` files (use `.env.sample` as template)
- `data/db.sqlite3` (development database)
- `media/` user uploads
- API keys or secrets

## Database

### Migrations

```bash
cd backend

# Create migrations
uv run python manage.py makemigrations

# Apply migrations
uv run python manage.py migrate

# Show migration status
uv run python manage.py showmigrations
```

### Models Location

Each Django app has its own `models.py`. Key models:

- `portfolios/models.py`: Portfolio
- `companies/models.py`: Company
- `shares_transactions/models.py`: SharesTransaction
- `dividends_transactions/models.py`: DividendsTransaction

## Background Tasks (Celery)

```bash
# Start Celery worker
celery -A buho_backend.celery_app:app worker -l info
```

Tasks are used for:

- Fetching stock prices
- Fetching exchange rates
- Long-running calculations

## Docker Development

```bash
# Build and run with docker-compose
docker-compose -f docker-compose.dev.yml up --build

# Production setup
docker-compose up --build
```

## Common Tasks

### Adding a New Django App

```bash
cd backend
uv run python manage.py startapp myapp
# Add 'myapp' to INSTALLED_APPS in buho_backend/settings.py
```

### Adding Frontend Components

- Components go in `client/src/components/`
- Pages go in `client/src/pages/`
- API hooks go in `client/src/hooks/`

### Fetching Stock Data

The app uses `yfinance` for stock prices. Rate limiting is handled via `requests-ratelimiter`.

## Troubleshooting

### Backend Issues

- **Import errors**: Ensure `PYTHONPATH` includes project root
- **Database errors**: Run migrations (`uv run python manage.py migrate`)
- **Redis connection**: Ensure Redis is running (`redis-server`)

### Frontend Issues

- **Type errors**: Check `tsconfig.json` configuration
- **Build errors**: Clear `node_modules` and reinstall (`rm -rf node_modules && npm install`)

## Useful Commands Reference

```bash
# Backend
cd backend
uv sync --all-extras              # Install dependencies
uv run python manage.py runserver # Start dev server
uv run python manage.py test      # Run tests
uv run ruff format .              # Format code
uv run ruff check . --fix         # Lint and auto-fix
uv run mypy .                     # Type check

# Frontend
cd client
npm install                       # Install dependencies
npm start                          # Start dev server
npm test                           # Run tests
npm run lint                       # Lint code
npm run build                      # Production build
```
