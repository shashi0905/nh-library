# Neighborhood Library App — Implementation Plan

**Date:** 2026-05-15  
**Version:** 1.0  
**Reference:** HIGH_LEVEL_DESIGN.md

---

## Overview

The build is divided into **6 phases**. Each phase produces a working, testable increment. CI/CD is introduced in Phase 2 and hardened progressively. No phase leaves the codebase in a broken state.

```
Phase 1 → Project scaffold + coding standards tooling
Phase 2 → Database layer + migrations + CI pipeline
Phase 3 → Backend service + REST API + unit/integration tests
Phase 4 → gRPC transport + extended features + background tasks
Phase 5 → Next.js frontend
Phase 6 → Containerisation (prod) + CD pipeline + observability
```

---

## Phase 1 — Project Scaffold & Coding Standards

**Goal:** Empty repo → runnable skeleton with all linting/formatting gates in place.  
**Output:** Developers can clone, install, and run `pre-commit` + `lint` + `typecheck` with zero errors.

### 1.1 Repository Initialisation

- Create Git repo; add `.gitignore` (Python, Node, Docker, IDE files).
- Establish branch strategy: `main` (protected) ← `develop` ← feature branches.
- Add `CODEOWNERS` file.

### 1.2 Backend Scaffold

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # bare FastAPI() instance, /health endpoint
│   └── config.py        # pydantic-settings BaseSettings
├── tests/
│   └── __init__.py
├── .env.example
├── pyproject.toml       # project metadata + tool config (single source of truth)
└── requirements/
    ├── base.txt         # runtime deps (pinned exact versions)
    ├── dev.txt          # pytest, ruff, mypy, pre-commit
    └── prod.txt         # base + gunicorn/uvicorn workers
```

**Tooling configured in `pyproject.toml`:**

| Tool | Purpose | Config key |
|---|---|---|
| `ruff` | Linting + import sorting | `[tool.ruff]` |
| `black` | Code formatting | `[tool.black]` |
| `mypy` | Static type checking (strict) | `[tool.mypy]` |
| `pytest` | Test runner | `[tool.pytest.ini_options]` |
| `coverage` | Coverage reporting (≥ 80% gate) | `[tool.coverage]` |

**Pre-commit hooks (`.pre-commit-config.yaml`):**
- `ruff --fix`
- `black --check`
- `mypy`
- `detect-secrets` (blocks accidental credential commits)
- `check-merge-conflict`

### 1.3 Frontend Scaffold

```bash
npx create-next-app@14 frontend \
  --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
```

Add to `frontend/`:
- `eslint` + `prettier` config
- `@typescript-eslint` strict rules
- Husky + lint-staged for pre-commit on `.ts/.tsx`

### 1.4 Root-level Tooling

- `docker-compose.yml` — `db` service only (postgres:16-alpine) for local dev
- `Makefile` with targets: `install`, `lint`, `typecheck`, `test`, `dev`, `migrate`

### Standards Established in This Phase

- All Python files must pass `ruff`, `black`, `mypy --strict`.
- All TypeScript files must pass `eslint` + `prettier`.
- No secrets in source; `.env.example` documents every variable.
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `chore:`, etc.).

---

## Phase 2 — Database Layer + Migrations + CI Pipeline

**Goal:** Schema defined in code, migrations runnable, CI catches regressions on every push.  
**Output:** `make migrate` creates all tables; CI pipeline runs lint + tests on every PR.

### 2.1 SQLAlchemy Models

Create `app/db/base.py`:
- Async engine (`create_async_engine`) + `AsyncSession` factory.
- `Base` declarative class with shared columns: `id` (UUID v7), `created_at`, `updated_at`.

Create ORM models:

**`app/db/models/book.py`**
```
Book: id, isbn (unique), title, author, total_copies, available, search_vector (tsvector), created_at, updated_at
```

**`app/db/models/member.py`**
```
Member: id, name, email (unique), phone, joined_at, is_active, created_at, updated_at
```

**`app/db/models/loan.py`**
```
Loan: id, book_id (FK), member_id (FK), borrowed_at, due_date, returned_at,
      status (ENUM: ACTIVE/RETURNED/OVERDUE), fine_amount (Numeric), fine_paid, created_at
```

Indexes:
- `books.isbn` — unique
- `books.search_vector` — GIN index for full-text search
- `loans(member_id, status)` — composite for member loan queries
- `loans(due_date)` — for overdue detection queries

### 2.2 Alembic Setup

```bash
alembic init alembic
```

- Configure `alembic/env.py` to use async engine and import all models.
- Generate initial migration: `alembic revision --autogenerate -m "initial_schema"`.
- Add `tsvector` trigger migration manually (not auto-detectable).
- Document: `make migrate` = `alembic upgrade head`.

### 2.3 Repository Interfaces (ABCs)

Create `app/repositories/base.py` — abstract `IRepository[T]` with:
- `get(id)`, `list(filters, cursor, limit)`, `create(data)`, `update(id, data)`, `delete(id)`

Create concrete implementations:
- `app/repositories/book_repo.py`
- `app/repositories/member_repo.py`
- `app/repositories/loan_repo.py`

Each repo takes `AsyncSession` via constructor injection (no global state).

### 2.4 Unit Tests — Repository Layer

```
tests/
├── conftest.py          # Testcontainers PostgreSQL fixture, async session fixture
├── unit/
│   └── test_models.py   # Model instantiation, constraint checks
└── integration/
    └── test_repos.py    # CRUD against real DB via Testcontainers
```

- `conftest.py` spins up `postgres:16-alpine` via Testcontainers, runs migrations, yields session.
- Each test runs in a transaction that is rolled back after the test (fast, isolated).

### 2.5 CI Pipeline — GitHub Actions

**File:** `.github/workflows/ci.yml`  
**Triggers:** `push` to any branch, `pull_request` to `develop` or `main`

```
Jobs (run in parallel where possible):

backend-lint
  └── ruff, black --check, mypy --strict

backend-test
  └── pytest (unit + integration) with Testcontainers
  └── coverage report — fail if < 80%

frontend-lint
  └── eslint, tsc --noEmit, prettier --check

dependency-audit
  └── pip-audit (Python), npm audit (Node)
```

**Branch protection rules on `main` and `develop`:**
- All CI jobs must pass before merge.
- At least 1 reviewer approval required.
- No direct pushes.

---

## Phase 3 — Backend REST API + Business Logic + Tests

**Goal:** All REST endpoints working, business rules enforced, fully tested.  
**Output:** `make dev` starts the API; all endpoints callable via `/docs`; test suite green.

### 3.1 Pydantic Schemas

Create request/response schemas in `app/schemas/`:

**`book.py`:** `BookCreate`, `BookUpdate`, `BookResponse`, `BookListResponse`  
**`member.py`:** `MemberCreate`, `MemberUpdate`, `MemberResponse`  
**`loan.py`:** `LoanCreate`, `LoanReturnResponse`, `LoanResponse`, `LoanListResponse`

Rules:
- All schemas use `model_config = ConfigDict(strict=True, from_attributes=True)`.
- ISBN validated with a custom `@field_validator` (ISBN-13 check digit).
- Email validated via `pydantic.EmailStr`.
- `BookUpdate` / `MemberUpdate` use `Optional` fields (partial update pattern).

### 3.2 Domain Exceptions

`app/exceptions.py` — define domain exceptions:
```
BookNotFound, MemberNotFound, LoanNotFound
BookNotAvailable       # available == 0
MemberInactive         # is_active == False
LoanAlreadyReturned
DuplicateISBN
DuplicateEmail
```

`app/main.py` — register exception handlers that map each to the correct HTTP status + RFC 7807 error body.

### 3.3 Service Layer

**`app/services/book_service.py`**
- `create_book`, `update_book`, `get_book`, `list_books`, `deactivate_book`
- `list_books` delegates full-text search to repo when `q` param present.

**`app/services/member_service.py`**
- `register_member`, `update_member`, `get_member`, `list_members`
- `get_member` includes active loans in response.

**`app/services/loan_service.py`**
- `borrow_book`: validates member active, book available; decrements `available` inside `SELECT FOR UPDATE` transaction.
- `return_book`: sets `returned_at`, computes fine if overdue, sets status `RETURNED`.
- `list_loans`: supports filters `member_id`, `status`, `overdue`.
- `pay_fine`: sets `fine_paid = True`.

Services receive repository instances via constructor — no direct DB imports.

### 3.4 API Routers

**`app/api/deps.py`**
- `get_db()` — yields `AsyncSession` per request.
- `get_current_user()` — decodes JWT, returns user payload.
- `require_staff()` — asserts role == STAFF.

**`app/api/v1/books.py`** — 5 endpoints (see HLD §4)  
**`app/api/v1/members.py`** — 4 endpoints  
**`app/api/v1/loans.py`** — 5 endpoints  
**`app/api/v1/router.py`** — aggregates all three with prefix `/api/v1`

Each router function is thin: validate input → call service → return schema. No business logic.

### 3.5 Authentication

`app/auth/`:
- `jwt.py` — `create_access_token`, `decode_token` using `python-jose`.
- `router.py` — `POST /api/v1/auth/token` (login), `POST /api/v1/auth/refresh`.
- Passwords hashed with `bcrypt` via `passlib`.
- `users` table added (id, email, hashed_password, role ENUM: STAFF/MEMBER).
- New Alembic migration for `users` table.

### 3.6 Pagination

Cursor-based pagination helper in `app/core/pagination.py`:
- Encodes `(created_at, id)` as an opaque base64 cursor.
- All list endpoints accept `cursor` + `limit` (default 20, max 100).
- Response includes `next_cursor` (null when no more pages).

### 3.7 Unit Tests — Service Layer

```
tests/unit/
├── test_book_service.py    # mock BookRepo; test create, duplicate ISBN, not-found
├── test_member_service.py  # mock MemberRepo; test register, inactive guard
└── test_loan_service.py    # mock LoanRepo + BookRepo; test borrow, return, fine calc,
                            # BookNotAvailable, LoanAlreadyReturned
```

- Repos mocked with `unittest.mock.AsyncMock`.
- No database required — pure logic tests.
- Target: 100% branch coverage on service layer.

### 3.8 Integration Tests — API Layer

```
tests/integration/
├── test_books_api.py    # full HTTP round-trip via httpx.AsyncClient
├── test_members_api.py
└── test_loans_api.py    # borrow → return → fine flow; concurrent borrow race condition test
```

- Uses `httpx.AsyncClient` with `app` as transport (no real network).
- Testcontainers PostgreSQL; migrations applied once per session.
- Auth tokens generated in fixtures.

### 3.9 CI Update

Add to `ci.yml`:
- Coverage badge generated and committed to `README.md`.
- `pytest --tb=short -q` output uploaded as artifact on failure.

---

## Phase 4 — gRPC Transport + Extended Features + Background Tasks

**Goal:** gRPC-Web transport available alongside REST; overdue detection running; sample client script working.  
**Output:** Both `/api/v1/*` (REST) and gRPC port respond to requests using the same service layer.

### 4.1 Protobuf Definition

`backend/proto/library.proto` — define all messages and service (see HLD §5).

Generate Python stubs:
```bash
python -m grpc_tools.protoc \
  -I proto \
  --python_out=app/grpc/generated \
  --grpc_python_out=app/grpc/generated \
  proto/library.proto
```

Add generation step to `Makefile`: `make proto`.

### 4.2 gRPC Servicer

`app/grpc/servicer.py` — implements the generated `LibraryServiceServicer`:
- Each method: deserialise Protobuf request → call the **same service layer** used by REST → serialise response.
- Error mapping: domain exceptions → `grpc.StatusCode` (e.g., `NOT_FOUND`, `ALREADY_EXISTS`).

`app/grpc/server.py` — standalone gRPC server on port `50051`.

Both servers (FastAPI on `8000`, gRPC on `50051`) started from `app/main.py` using `asyncio.gather`.

### 4.3 Background Task — Overdue Detection

`app/tasks/overdue.py`:
- APScheduler `AsyncIOScheduler`, cron trigger: daily at 00:05.
- Query: `loans WHERE status = ACTIVE AND due_date < now()`.
- Batch update: `status = OVERDUE`, compute `fine_amount = days_overdue × FINE_RATE_PER_DAY`.
- `FINE_RATE_PER_DAY` read from settings (default: `1.00`).
- Scheduler registered on FastAPI `startup` event, shut down on `shutdown`.

### 4.4 Sample Client Script

`backend/scripts/sample_client.py`:
- Uses `httpx` (REST) to exercise the full happy path:
  1. Login → get token
  2. Create book
  3. Register member
  4. Borrow book
  5. Return book (with fine if overdue)
  6. Pay fine
  7. List loans for member
- Prints each step with request/response summary.
- Runnable: `python scripts/sample_client.py --base-url http://localhost:8000`

### 4.5 Unit Tests — gRPC Servicer

```
tests/unit/test_grpc_servicer.py
```
- Mock service layer; assert correct Protobuf response fields.
- Assert correct `grpc.StatusCode` for each domain exception.

### 4.6 Unit Tests — Background Task

```
tests/unit/test_overdue_task.py
```
- Mock loan repo; assert correct loans are updated; assert fine calculation formula.

---

## Phase 5 — Next.js Frontend

**Goal:** Functional web UI for library staff covering all core operations.  
**Output:** `make dev` starts frontend at `localhost:3000`; all pages render and call the API.

### 5.1 Typed API Client

`frontend/src/lib/api.ts`:
- Thin `fetch` wrapper with base URL from `NEXT_PUBLIC_API_URL` env var.
- Typed request/response interfaces mirroring backend Pydantic schemas.
- Centralised error handling: non-2xx → throws typed `ApiError`.
- Auth token stored in `httpOnly` cookie (set via Next.js route handler, not localStorage).

### 5.2 Pages & Components

**Layout:** Shared sidebar nav (Books / Members / Loans), header with logged-in user + logout.

| Route | Page | Key Components |
|---|---|---|
| `/` | Dashboard | Stats cards (total books, active loans, overdue count) |
| `/books` | Book list | Searchable table, pagination, "Add Book" button |
| `/books/[id]` | Book detail | Edit form, copy count, loan history |
| `/members` | Member list | Searchable table, pagination, "Register Member" |
| `/members/[id]` | Member detail | Edit form, active loans list |
| `/loans` | Loan list | Filter by status/member, overdue highlighted |
| `/loans/new` | Borrow form | Member + book selector, due date |
| `/login` | Login | Email + password form |

**Shared components:**
- `DataTable` — sortable, paginated, cursor-aware
- `FormField` — label + input + error message
- `StatusBadge` — colour-coded ACTIVE / RETURNED / OVERDUE
- `ConfirmDialog` — used for destructive actions

### 5.3 State Management

- Server Components for data fetching (Next.js App Router default).
- Client Components only where interactivity required (forms, modals).
- No global state library needed — React `useActionState` + Server Actions for mutations.

### 5.4 Accessibility & Standards

- All interactive elements keyboard-navigable.
- ARIA labels on icon-only buttons.
- Colour contrast meets WCAG 2.1 AA.
- `next/image` for all images; `next/font` for fonts.

### 5.5 Frontend Tests

```
frontend/src/__tests__/
├── components/
│   ├── DataTable.test.tsx
│   ├── StatusBadge.test.tsx
│   └── FormField.test.tsx
└── lib/
    └── api.test.ts          # mock fetch; assert correct URL, headers, error handling
```

- Jest + React Testing Library.
- `npm test` runs all; `npm run test:coverage` enforces ≥ 80%.

### 5.6 CI Update

Add `frontend-test` job to `ci.yml`:
```
frontend-test
  └── jest --coverage
  └── fail if coverage < 80%
```

---

## Phase 6 — Production Containerisation + CD Pipeline + Observability

**Goal:** One-command production deployment; full observability; automated deploy on merge to `main`.  
**Output:** `docker compose -f docker-compose.prod.yml up` starts the full production stack.

### 6.1 Production Dockerfiles

**`backend/Dockerfile`** (multi-stage):
```
Stage 1 (builder): python:3.12-slim → install deps into /venv
Stage 2 (runtime): python:3.12-slim → copy /venv, copy app, non-root user
CMD: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**`frontend/Dockerfile`** (multi-stage):
```
Stage 1 (deps):    node:20-alpine → npm ci
Stage 2 (builder): next build
Stage 3 (runtime): node:20-alpine → copy .next/standalone, non-root user
```

Security hardening in both:
- Non-root user (`appuser`).
- Read-only filesystem where possible.
- No dev dependencies in final image.
- `HEALTHCHECK` instruction.

### 6.2 Docker Compose Files

**`docker-compose.yml`** (development):
```yaml
services:
  db:        postgres:16-alpine  (volume-mounted data, port 5432 exposed)
  backend:   build context, volume-mount src, uvicorn --reload
  frontend:  build context, volume-mount src, next dev
  adminer:   adminer:latest      (dev DB UI, port 8080)
```

**`docker-compose.prod.yml`** (production):
```yaml
services:
  db:        postgres:16-alpine  (no exposed port, internal network only)
  backend:   pre-built image, 4 uvicorn workers, resource limits
  frontend:  pre-built image, resource limits
  nginx:     nginx:alpine        (reverse proxy, TLS termination, rate limiting)
```

### 6.3 Observability

**Structured Logging (`structlog`):**
- Every request logged: method, path, status, duration, request_id (UUID injected via middleware).
- Log level controlled by `LOG_LEVEL` env var.
- JSON format in production; human-readable in development.

**Prometheus Metrics (`prometheus-fastapi-instrumentator`):**
- Auto-instruments all FastAPI routes.
- Exposes `/metrics` (scrape endpoint).
- Key metrics: `http_requests_total`, `http_request_duration_seconds`.

**Health Endpoints:**
- `GET /health` — liveness (returns 200 if process alive).
- `GET /health/ready` — readiness (checks DB connection).

### 6.4 CD Pipeline — GitHub Actions

**File:** `.github/workflows/cd.yml`  
**Trigger:** Push to `main` (after CI passes)

```
Jobs:

build-and-push
  ├── docker build backend → push to registry (tagged: sha + latest)
  └── docker build frontend → push to registry

deploy-staging
  ├── depends_on: build-and-push
  ├── SSH to staging server (or ECS deploy)
  ├── docker compose pull && docker compose up -d
  └── Run smoke tests (curl /health/ready)

deploy-production
  ├── depends_on: deploy-staging
  ├── Requires manual approval (GitHub Environment protection rule)
  ├── Same deploy steps as staging
  └── Post-deploy: notify Slack / create GitHub Release
```

**Secrets managed via GitHub Actions Secrets:**
- `REGISTRY_TOKEN`, `STAGING_SSH_KEY`, `PROD_SSH_KEY`, `SLACK_WEBHOOK`

### 6.5 Environment Configuration

`.env.example` documents all variables:

```
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/library
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Auth
SECRET_KEY=<generate with: openssl rand -hex 32>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Loans
LOAN_DURATION_DAYS=14
FINE_RATE_PER_DAY=1.00

# Observability
LOG_LEVEL=INFO

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 6.6 README

`README.md` covers:
1. Prerequisites (Docker, Docker Compose, Python 3.12, Node 20)
2. Quick start: `git clone` → `cp .env.example .env` → `make dev`
3. Running migrations: `make migrate`
4. Running tests: `make test`
5. Generating proto stubs: `make proto`
6. API docs: `http://localhost:8000/docs`
7. Environment variable reference
8. Architecture diagram (link to HLD)

---

## Phase Summary

| Phase | Deliverable | CI/CD Gate |
|---|---|---|
| 1 | Scaffold + linting/formatting tooling | Pre-commit hooks |
| 2 | DB models + migrations + repo layer | CI: lint + unit tests on every PR |
| 3 | Full REST API + auth + pagination + tests | CI: lint + unit + integration + coverage ≥ 80% |
| 4 | gRPC transport + overdue tasks + sample client | CI: all previous + gRPC tests |
| 5 | Next.js frontend + frontend tests | CI: all previous + frontend lint + jest |
| 6 | Prod Docker + CD pipeline + observability | CD: auto-deploy staging; manual-approve prod |

---

## Coding Standards Checklist (enforced throughout all phases)

- [ ] All Python typed; `mypy --strict` passes with zero errors
- [ ] All functions/classes have docstrings (Google style)
- [ ] No magic numbers — constants in `app/core/constants.py` or settings
- [ ] No bare `except:` — always catch specific exceptions
- [ ] All DB operations async; no blocking calls in async context
- [ ] Repository layer has no business logic; service layer has no SQL
- [ ] Every new endpoint has at least one unit test and one integration test
- [ ] No secrets in source code or logs
- [ ] All list endpoints paginated (no unbounded queries)
- [ ] Migrations are reversible (`downgrade` implemented)
- [ ] Docker images run as non-root
- [ ] Conventional Commits on all commits
