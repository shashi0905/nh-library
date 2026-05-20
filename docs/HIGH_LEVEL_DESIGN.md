# Neighborhood Library App — High-Level Design

**Date:** 2026-05-13  
**Version:** 1.0

---

## 1. Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI (REST + OpenAPI) |
| API Protocol | REST/JSON (primary) + gRPC-Web via Protobuf (optional transport) |
| Database | PostgreSQL 16 |
| ORM / Migrations | SQLAlchemy 2 (async) + Alembic |
| Validation | Pydantic v2 |
| Frontend | Next.js 14 (App Router, TypeScript) |
| Containerisation | Docker + Docker Compose |
| Auth | JWT (Bearer tokens) via `python-jose` |
| Testing | pytest + pytest-asyncio, Testcontainers |
| Observability | Structured JSON logging (structlog), Prometheus metrics endpoint |

---

## 2. Project Structure

```
library/
├── backend/
│   ├── alembic/                  # DB migrations
│   ├── app/
│   │   ├── main.py               # FastAPI app factory
│   │   ├── config.py             # Settings (pydantic-settings)
│   │   ├── db/
│   │   │   ├── base.py           # SQLAlchemy engine + session
│   │   │   └── models/           # ORM models
│   │   │       ├── book.py
│   │   │       ├── member.py
│   │   │       └── loan.py
│   │   ├── api/
│   │   │   ├── deps.py           # Shared dependencies (DB session, auth)
│   │   │   └── v1/
│   │   │       ├── router.py     # Aggregates all routers
│   │   │       ├── books.py
│   │   │       ├── members.py
│   │   │       └── loans.py
│   │   ├── schemas/              # Pydantic request/response models
│   │   │   ├── book.py
│   │   │   ├── member.py
│   │   │   └── loan.py
│   │   ├── services/             # Business logic (pure, no HTTP/DB imports)
│   │   │   ├── book_service.py
│   │   │   ├── member_service.py
│   │   │   └── loan_service.py
│   │   └── exceptions.py         # Domain exceptions → HTTP error mapping
│   ├── proto/
│   │   └── library.proto         # Protobuf definitions (gRPC-Web)
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                  # Next.js App Router pages
│   │   │   ├── books/
│   │   │   ├── members/
│   │   │   └── loans/
│   │   ├── components/           # Reusable UI components
│   │   ├── lib/
│   │   │   └── api.ts            # Typed API client (fetch wrapper)
│   │   └── types/                # Shared TypeScript types
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## 3. Database Schema

```
┌──────────────┐        ┌──────────────────┐        ┌──────────────┐
│    books     │        │      loans       │        │   members    │
├──────────────┤        ├──────────────────┤        ├──────────────┤
│ id (PK)      │◄───────│ book_id (FK)     │───────►│ id (PK)      │
│ isbn (UNIQUE)│        │ member_id (FK)   │        │ email (UNIQ) │
│ title        │        │ borrowed_at      │        │ name         │
│ author       │        │ due_date         │        │ phone        │
│ total_copies │        │ returned_at      │        │ joined_at    │
│ available    │        │ fine_amount      │        │ is_active    │
│ created_at   │        │ fine_paid        │        │ created_at   │
│ updated_at   │        │ status (ENUM)    │        │ updated_at   │
└──────────────┘        │ created_at       │        └──────────────┘
                        └──────────────────┘

loan.status ENUM: ACTIVE | RETURNED | OVERDUE
```

### Design Decisions

- `books.available` is a derived counter (`total_copies` − active loans), updated transactionally to prevent race conditions under concurrent borrows.
- `loans.fine_amount` is computed on return based on overdue days × daily rate (configurable via environment variable).
- All PKs are UUIDs v7 (time-ordered, index-friendly).
- Soft-delete via `is_active` on members; books are guarded by `available = 0` check.
- Full-text search on books via PostgreSQL `tsvector` index on `title` + `author`.

---

## 4. REST API Endpoints

### Books — `/api/v1/books`

| Method | Path | Description |
|---|---|---|
| GET | `/` | List books (filter: `title`, `author`, `available_only`) |
| POST | `/` | Create book |
| GET | `/{id}` | Get book detail |
| PATCH | `/{id}` | Update book |
| DELETE | `/{id}` | Deactivate book |

### Members — `/api/v1/members`

| Method | Path | Description |
|---|---|---|
| GET | `/` | List members |
| POST | `/` | Register member |
| GET | `/{id}` | Get member + active loans |
| PATCH | `/{id}` | Update member |

### Loans — `/api/v1/loans`

| Method | Path | Description |
|---|---|---|
| POST | `/` | Borrow a book |
| PATCH | `/{id}/return` | Return a book |
| GET | `/` | List loans (filter: `member_id`, `status`, `overdue`) |
| GET | `/{id}` | Loan detail |
| POST | `/{id}/pay-fine` | Mark fine as paid |

---

## 5. gRPC / Protobuf Definition

```protobuf
syntax = "proto3";
package library.v1;

service LibraryService {
  rpc CreateBook(CreateBookRequest) returns (BookResponse);
  rpc UpdateBook(UpdateBookRequest) returns (BookResponse);
  rpc GetBook(GetBookRequest)       returns (BookResponse);
  rpc ListBooks(ListBooksRequest)   returns (ListBooksResponse);

  rpc CreateMember(CreateMemberRequest) returns (MemberResponse);
  rpc UpdateMember(UpdateMemberRequest) returns (MemberResponse);
  rpc GetMember(GetMemberRequest)       returns (MemberResponse);

  rpc BorrowBook(BorrowBookRequest)   returns (LoanResponse);
  rpc ReturnBook(ReturnBookRequest)   returns (LoanResponse);
  rpc ListLoans(ListLoansRequest)     returns (ListLoansResponse);
}
```

> The REST server and gRPC server share the same service layer — only the transport adapter differs.

---

## 6. Layered Architecture

```
HTTP Request / gRPC Call
        │
        ▼
  ┌─────────────┐
  │  API Layer  │  ← FastAPI routers / gRPC servicer
  │  (thin)     │    Input validation (Pydantic), auth, rate-limit
  └──────┬──────┘
         │ calls
         ▼
  ┌─────────────┐
  │  Service    │  ← Pure business logic
  │  Layer      │    Borrow rules, overdue detection, fine calc
  └──────┬──────┘
         │ calls
         ▼
  ┌─────────────┐
  │ Repository  │  ← SQLAlchemy async queries
  │  Layer      │    No business logic here
  └──────┬──────┘
         │
         ▼
     PostgreSQL
```

This separation ensures:
- Services are unit-testable without a database.
- Swapping PostgreSQL only touches the repository layer.
- REST and gRPC transports share identical business logic.

---

## 7. Optional / Extended Features

| Feature | Implementation |
|---|---|
| Overdue detection | Background task (APScheduler) runs nightly; sets `loan.status = OVERDUE` and computes `fine_amount` |
| Fine tracking | `fine_amount` (Decimal), `fine_paid` (bool) on loan; dedicated `pay-fine` endpoint |
| Due dates | `due_date` set at borrow time (default: 14 days, configurable via env var) |
| Borrow conflict guard | Service-level check + `SELECT ... FOR UPDATE` on `books.available` to prevent double-borrow under concurrency |
| Input validation | Pydantic v2 strict mode; ISBN-13 format validation; email format validation |
| Authentication | JWT Bearer tokens; roles: `STAFF` (full access), `MEMBER` (read + own loans only) |
| Pagination | Cursor-based pagination on all list endpoints |
| Full-text search | PostgreSQL `tsvector` on `books.title` + `books.author` |
| Sample client script | `backend/scripts/sample_client.py` — exercises all endpoints end-to-end |
| OpenAPI docs | Auto-generated at `/docs` (Swagger UI) and `/redoc` |
| Prometheus metrics | `/metrics` endpoint — request count, latency histograms per endpoint |

---

## 8. Design Principles

### SOLID
- **Single Responsibility:** Router ≠ Service ≠ Repository — each layer has one reason to change.
- **Open/Closed:** New loan rules (e.g., member tier limits) added via strategy pattern in the service layer without modifying existing code.
- **Dependency Inversion:** Services depend on repository interfaces (ABCs), not concrete SQLAlchemy classes.

### 12-Factor App (production-grade, scalable)
- All config via environment variables (`pydantic-settings`; `.env` for local dev).
- Stateless API servers — scale horizontally behind a load balancer with no shared in-process state.
- DB connection pooling via asyncpg pool (`POOL_SIZE`, `MAX_OVERFLOW` configurable).
- Structured JSON logs to stdout — compatible with any log aggregator (CloudWatch, Datadog, ELK).

### Scalability
- Async I/O throughout (FastAPI + asyncpg) — high concurrency on a single instance.
- `books.available` updated with `SELECT ... FOR UPDATE` — safe under concurrent borrow requests.
- Stateless design → add API replicas without coordination.
- DB read replicas supported by routing read-only queries to a secondary connection string.

---

## 9. Testing Strategy

| Level | Tool | Scope |
|---|---|---|
| Unit | pytest | Service layer with mocked repositories |
| Integration | pytest + Testcontainers | Real PostgreSQL; tests full request → DB round-trip |
| Contract | Pydantic schema assertions | Validates REST schemas align with Protobuf definitions |
| API smoke | `sample_client.py` | End-to-end happy-path and error-path scenarios |

---

## 10. Docker Compose (Development)

```yaml
services:
  db:        postgres:16-alpine
  backend:   Python/FastAPI  (uvicorn --reload)
  frontend:  Next.js         (next dev)
  adminer:   Adminer         (lightweight DB UI — dev only)
```

**Production:** Each service is an independent Docker image pushed to a registry and deployed to ECS/Kubernetes with separate auto-scaling policies per service tier.

---

## 11. Summary

The design delivers a clean 3-layer backend (API → Service → Repository) where the service layer is shared by both REST and gRPC transports. The PostgreSQL schema is fully normalised with concurrency-safe borrow logic. The Next.js frontend consumes the REST API via a typed client. All optional features — fines, overdue tracking, JWT auth, full-text search, and observability — are first-class concerns built into the architecture from the start. The stateless, async design allows the API tier to scale horizontally with zero code changes.
