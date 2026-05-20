# Technical Architecture Document

## Overview

The Neighborhood Library application is a full-stack web application built with a modern tech stack. It consists of a FastAPI backend, a Next.js frontend, and a PostgreSQL database, all containerized using Docker Compose for easy deployment and development.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Browser                          │
│                    (React/Next.js Frontend)                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTPS/HTTP
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Docker Compose Network                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Nginx (Optional)                      │  │
│  │              Reverse Proxy / Load Balancer               │  │
│  └─────────────────────────┬────────────────────────────────┘  │
│                           │                                    │
│  ┌────────────────────────┴────────────────────────────────┐  │
│  │                                                          │  │
│  │  ┌──────────────────────┐  ┌──────────────────────┐     │  │
│  │  │   Frontend Container │  │  Backend Container   │     │  │
│  │  │   (Next.js App)      │  │   (FastAPI App)      │     │  │
│  │  │   Port: 3000         │  │   Port: 8000         │     │  │
│  │  └──────────┬───────────┘  └──────────┬───────────┘     │  │
│  │             │                          │                  │  │
│  │             │ REST API                │                  │  │
│  │             │                          │                  │  │
│  │             └──────────────────────────┘                  │  │
│  │                          │                                │  │
│  │  ┌───────────────────────┴────────────────────────────┐  │  │
│  │  │                                                      │  │
│  │  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  │         Database Container                    │  │  │
│  │  │  │         (PostgreSQL)                          │  │  │
│  │  │  │         Port: 5432                            │  │  │
│  │  │  └──────────────────────────────────────────────┘  │  │
│  │  │                                                      │  │
│  │  └──────────────────────────────────────────────────────┘  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### High-Level Components

1. **Frontend (Next.js)**
   - React-based single-page application
   - Server-side rendering with Next.js App Router
   - TailwindCSS for styling
   - Client-side authentication state management

2. **Backend (FastAPI)**
   - RESTful API with async/await support
   - JWT-based authentication
   - Pydantic for data validation
   - SQLAlchemy ORM with async support

3. **Database (PostgreSQL)**
   - Relational database for persistent storage
   - Docker volume for data persistence
   - Supports complex queries and transactions

## Low-Level Component Interaction

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Frontend (Next.js)                              │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                        Pages & Components                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │  Dashboard   │  │   Books      │  │   Members    │             │  │
│  │  │  (page.tsx)  │  │  (page.tsx)  │  │  (page.tsx)  │             │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │  │
│  │         │                  │                  │                      │  │
│  │         └──────────────────┴──────────────────┘                      │  │
│  │                            │                                         │  │
│  │  ┌─────────────────────────┴─────────────────────────────┐          │  │
│  │  │              Shared Components                         │          │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │          │  │
│  │  │  │  DataTable   │  │  FormField   │  │ StatusBadge  │ │          │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘ │          │  │
│  │  └─────────────────────────┬─────────────────────────────┘          │  │
│  │                            │                                         │  │
│  │  ┌─────────────────────────┴─────────────────────────────┐          │  │
│  │  │              Auth Components                           │          │  │
│  │  │  ┌──────────────┐  ┌──────────────┐                  │          │  │
│  │  │  │ AuthProvider │  │Authenticated │                  │          │  │
│  │  │  │  (Context)   │  │   Layout     │                  │          │  │
│  │  │  └──────────────┘  └──────────────┘                  │          │  │
│  │  └─────────────────────────┬─────────────────────────────┘          │  │
│  │                            │                                         │  │
│  │  ┌─────────────────────────┴─────────────────────────────┐          │  │
│  │  │              API Client Layer                          │          │  │
│  │  │  ┌──────────────────────────────────────────────┐    │          │  │
│  │  │  │  api.ts (fetchWithAuth helper)               │    │          │  │
│  │  │  │  - booksApi                                  │    │          │  │
│  │  │  │  - membersApi                                │    │          │  │
│  │  │  │  - loansApi                                  │    │          │  │
│  │  │  │  - authApi                                   │    │          │  │
│  │  │  └──────────────────────────────────────────────┘    │          │  │
│  │  └─────────────────────────┬─────────────────────────────┘          │  │
│  └────────────────────────────┼───────────────────────────────────────┘  │
│                                 │                                          │
│                                 │ HTTP/JSON                                 │
│                                 │ Authorization: Bearer <token>            │
│                                 ▼                                          │
└─────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────┐
│                         Backend (FastAPI)                                │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                        API Router Layer                              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │ /api/v1/auth │  │ /api/v1/books│  │/api/v1/members│            │  │
│  │  │   (auth.py)  │  │  (books.py)  │  │ (members.py) │            │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │  │
│  │         │                  │                  │                      │  │
│  │         └──────────────────┴──────────────────┘                      │  │
│  │                            │                                         │  │
│  │  ┌─────────────────────────┴─────────────────────────────┐          │  │
│  │  │              Dependencies Layer                         │          │  │
│  │  │  ┌──────────────┐  ┌──────────────┐                  │          │  │
│  │  │  │  get_db      │  │ require_staff│                  │          │  │
│  │  │  │  (Database)  │  │  (Auth)      │                  │          │  │
│  │  │  └──────────────┘  └──────────────┘                  │          │  │
│  │  └─────────────────────────┬─────────────────────────────┘          │  │
│  │                            │                                         │  │
│  │  ┌─────────────────────────┴─────────────────────────────┐          │  │
│  │  │              Service Layer                              │          │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │          │  │
│  │  │  │BookService   │  │MemberService │  │ LoanService  │ │          │  │
│  │  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │          │  │
│  │  └─────────┼──────────────────┼──────────────────┼─────────┘          │  │
│  │            │                  │                  │                     │  │
│  │  ┌─────────┴──────────────────┴──────────────────┴─────────┐          │  │
│  │  │              Repository Layer                            │          │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │          │  │
│  │  │  │BookRepo      │  │MemberRepo    │  │  LoanRepo    │ │          │  │
│  │  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │          │  │
│  │  └─────────┼──────────────────┼──────────────────┼─────────┘          │  │
│  └────────────┼──────────────────┼──────────────────┼────────────────────┘
│               │                  │                  │
│               │ SQLAlchemy ORM   │                  │
│               │                  │                  │
│  ┌────────────┴──────────────────┴──────────────────┴────────────────────┐  │
│  │                        Database Layer                                │  │
│  │  ┌──────────────────────────────────────────────────────────────┐    │  │
│  │  │              PostgreSQL Database                               │    │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │    │  │
│  │  │  │   books      │  │   members    │  │    loans     │       │    │  │
│  │  │  │   (table)    │  │   (table)    │  │   (table)    │       │    │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘       │    │  │
│  │  │  ┌──────────────┐  ┌──────────────┐                        │    │  │
│  │  │  │   users      │  │   roles      │                        │    │  │
│  │  │  │   (table)    │  │   (table)    │                        │    │  │
│  │  │  └──────────────┘  └──────────────┘                        │    │  │
│  │  └──────────────────────────────────────────────────────────────┘    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend Architecture

#### Pages (App Router)
- **Dashboard** (`src/app/page.tsx`): Overview with statistics
- **Books** (`src/app/books/page.tsx`): Book management interface
- **Members** (`src/app/members/page.tsx`): Member management interface
- **Loans** (`src/app/loans/page.tsx`): Loan tracking interface
- **Login** (`src/app/login/page.tsx`): Authentication page

#### Components
- **DataTable**: Reusable table with sorting and pagination
- **FormField**: Form input component with validation
- **StatusBadge**: Status indicator component
- **ConfirmDialog**: Modal confirmation dialog
- **AuthProvider**: React Context for authentication state
- **AuthenticatedLayout**: Layout wrapper for protected routes

#### API Client
- **api.ts**: Centralized API client with authentication
- **fetchWithAuth**: Helper function that adds JWT tokens to requests
- **booksApi**: Book-related API calls
- **membersApi**: Member-related API calls
- **loansApi**: Loan-related API calls
- **authApi**: Authentication API calls

### Backend Architecture

#### API Layer
- **Router** (`app/api/v1/router.py`): Main API router
- **Auth Router** (`app/api/v1/auth.py`): Authentication endpoints
- **Books Router** (`app/api/v1/books.py`): Book CRUD operations
- **Members Router** (`app/api/v1/members.py`): Member CRUD operations
- **Loans Router** (`app/api/v1/loans.py`): Loan management operations

#### Dependencies
- **get_db**: Database session dependency
- **require_staff**: Staff role verification dependency
- **TokenData**: JWT token validation

#### Service Layer
- **BookService**: Business logic for books
- **MemberService**: Business logic for members
- **LoanService**: Business logic for loans

#### Repository Layer
- **BookRepository**: Database operations for books
- **MemberRepository**: Database operations for members
- **LoanRepository**: Database operations for loans

#### Database Models
- **User**: User accounts with roles
- **Book**: Book inventory
- **Member**: Library members
- **Loan**: Book borrowing records
- **Role**: User roles (staff, member)

## Data Flow

### Authentication Flow
1. User submits credentials to `/api/v1/auth/token`
2. Backend validates credentials and returns JWT token
3. Frontend stores token in localStorage
4. Subsequent API calls include `Authorization: Bearer <token>` header
5. Backend validates token and checks user role for protected endpoints

### Book Creation Flow
1. User fills book creation form in frontend
2. Frontend calls `booksApi.create()` with book data
3. API client adds JWT token to request headers
4. Backend validates token and staff role
5. BookService validates ISBN and creates book
6. BookRepository saves to database
7. Response returned to frontend

### Loan Creation Flow
1. User selects member and book from dropdowns
2. Frontend calls `loansApi.create()` with member_id and book_id
3. API client adds JWT token to request headers
4. Backend validates token and staff role
5. LoanService checks book availability and member status
6. LoanRepository creates loan record
7. Response returned to frontend

## Technology Stack

### Frontend
- **Framework**: Next.js 16.2.6 (App Router)
- **UI Library**: React 18.3.1
- **Styling**: TailwindCSS 3.4.17
- **HTTP Client**: Native Fetch API
- **Testing**: Jest 29.7.0, React Testing Library
- **Linting**: ESLint 9.0.0, TypeScript ESLint 8.0.0
- **Formatting**: Prettier 3.5.3

### Backend
- **Framework**: FastAPI
- **ORM**: SQLAlchemy (async)
- **Database**: PostgreSQL
- **Authentication**: JWT (passlib)
- **Validation**: Pydantic
- **Testing**: pytest
- **Linting**: Ruff

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Reverse Proxy**: Nginx (optional for production)
- **Environment**: dotenv for configuration

## Security Considerations

### Authentication
- JWT-based authentication with httpOnly cookies
- Token stored in localStorage for API calls
- Staff role required for write operations
- Password hashing with passlib

### Authorization
- Role-based access control (staff vs member)
- Protected endpoints require staff role
- Public endpoints for listing resources

### Data Validation
- Pydantic schemas for request/response validation
- SQL injection prevention via ORM
- Input sanitization

## Deployment

### Development
```bash
docker-compose up
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up
```

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key
- `API_BASE_URL`: Backend API URL
