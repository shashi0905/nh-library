# Neighborhood Library

A modern library management system for tracking books, members, and lending operations. Built with a focus on simplicity and efficiency for small neighborhood libraries.

## Features

- **Book Management**: Add, update, and track book inventory with ISBN validation
- **Member Management**: Register and manage library members
- **Loan Management**: Track book borrowing, returns, and overdue fines
- **Authentication**: Secure JWT-based authentication for staff users
- **Dashboard**: Real-time statistics on books, members, and loans
- **Responsive UI**: Modern, user-friendly interface built with Next.js and TailwindCSS

## Tech Stack

### Backend
- **Framework**: FastAPI 0.130.0
- **Language**: Python 3.12
- **Database**: PostgreSQL 16
- **ORM**: SQLAlchemy 2.0 with async support
- **Authentication**: JWT (python-jose) with bcrypt password hashing
- **Validation**: Pydantic 2.11
- **Migration**: Alembic
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

### Frontend
- **Framework**: Next.js 16 (React 18)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State Management**: React Hooks
- **HTTP Client**: Native Fetch API with custom wrapper

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Database**: PostgreSQL 16 (Alpine)
- **Development**: Hot-reload for both frontend and backend

## Prerequisites

- Docker and Docker Compose installed
- Node.js 18+ (for local frontend development)
- Python 3.12+ (for local backend development)
- Git

## Quick Start with Docker

The easiest way to get started is using Docker Compose, which sets up both the backend API and PostgreSQL database.

### 1. Clone the Repository

```bash
git clone <repository-url>
cd nh-library
```

### 2. Start Services with Docker Compose

```bash
docker-compose up --build
```

This will:
- Start PostgreSQL database
- Build and start the FastAPI backend
- Run database migrations automatically
- Start the backend server on `http://localhost:8000`

### 3. Create Seed Staff User

After the services are running, execute the seed script to create a staff user:

```bash
docker-compose exec backend python scripts/seed_user.py
```

This will create a staff user with:
- **Email**: `staff@example.com`
- **Password**: `staff123`

### 4. Access the Application

- **Backend API**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **Database**: `localhost:5432`

## Frontend Setup

The frontend is a separate Next.js application that needs to be run locally.

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment Variables

Create a `.env.local` file in the frontend directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 4. Login

Use the seed user credentials:
- **Email**: `staff@example.com`
- **Password**: `staff123`

## Local Development Setup

If you prefer to run the backend locally instead of using Docker:

### Backend Setup

1. **Create Virtual Environment**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Dependencies**

```bash
pip install -r requirements/dev.txt
```

3. **Configure Environment Variables**

Create a `.env` file in the backend directory:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/library
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
LOAN_DURATION_DAYS=14
FINE_RATE_PER_DAY=1.00
LOG_LEVEL=INFO
```

4. **Start PostgreSQL**

Using Docker:
```bash
docker run -d \
  --name library-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=library \
  -p 5432:5432 \
  postgres:16-alpine
```

5. **Run Database Migrations**

```bash
alembic upgrade head
```

6. **Create Seed User**

```bash
python scripts/seed_user.py
```

7. **Start Backend Server**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

Follow the same steps as in the "Frontend Setup" section above.

## API Endpoints

### Authentication
- `POST /api/v1/auth/token` - Login and get access token
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/refresh` - Refresh access token

### Books
- `GET /api/v1/books` - List books (with pagination and search)
- `POST /api/v1/books` - Create a new book (staff only)
- `GET /api/v1/books/{id}` - Get book details
- `PATCH /api/v1/books/{id}` - Update book (staff only)
- `DELETE /api/v1/books/{id}` - Delete book (staff only)

### Members
- `GET /api/v1/members` - List members (with pagination)
- `POST /api/v1/members` - Register new member (staff only)
- `GET /api/v1/members/{id}` - Get member details
- `PATCH /api/v1/members/{id}` - Update member (staff only)

### Loans
- `GET /api/v1/loans` - List loans (with filters)
- `POST /api/v1/loans` - Borrow a book (staff only)
- `PATCH /api/v1/loans/{id}/return` - Return a book (staff only)
- `POST /api/v1/loans/{id}/pay-fine` - Pay fine (staff only)

## Database Schema

The application uses the following main entities:
- **users**: Staff users with authentication credentials
- **books**: Book inventory with ISBN, title, author, and copy tracking
- **members**: Library members with contact information
- **loans**: Book borrowing records with due dates and fine tracking

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Development Workflow

1. Make changes to the code
2. Backend changes auto-reload with Docker Compose
3. Frontend changes auto-reload with Next.js dev server
4. Run tests before committing
5. Use the API documentation at `/docs` to test endpoints manually

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running: `docker ps | grep library-db`
- Check database logs: `docker logs library-db`
- Verify connection string in `.env` file

### Backend Not Starting
- Check if port 8000 is already in use
- Verify Python dependencies are installed
- Check backend logs: `docker logs library-backend`

### Frontend Not Connecting to Backend
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Ensure backend is running on `http://localhost:8000`
- Check browser console for CORS errors

### Seed User Already Exists
The seed script will skip creation if the user already exists. You can safely run it multiple times.

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
