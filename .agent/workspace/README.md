# Task Management API

A RESTful Task Management API built with FastAPI, featuring JWT authentication, SQLAlchemy ORM, and comprehensive testing.

## Features

- ✅ FastAPI framework with auto-generated OpenAPI documentation
- ⏳ JWT-based authentication
- ⏳ SQLAlchemy ORM with SQLite database
- ⏳ CRUD operations for tasks with filtering and sorting
- ✅ Request/response validation with Pydantic
- ⏳ Comprehensive error handling
- ⏳ Pytest integration tests with 85%+ coverage

## Project Structure

```
.
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Core functionality and config
│   ├── db/            # Database configuration
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   └── main.py        # FastAPI application
├── tests/             # Test suite
├── requirements.txt   # Python dependencies
└── .env.example      # Environment variables template
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

4. Access the API documentation:
- OpenAPI (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run tests with coverage:
```bash
pytest --cov=app --cov-report=term-missing
```

## Development Status

### Completed
- ✅ Basic FastAPI project structure
- ✅ Configuration management with Pydantic Settings
- ✅ CORS middleware setup
- ✅ Health check and root endpoints
- ✅ Basic test setup

### In Progress
- ⏳ SQLAlchemy models for User and Task
- ⏳ JWT authentication system
- ⏳ Pydantic schemas for validation
- ⏳ CRUD operations for tasks
- ⏳ Filtering and sorting for tasks
- ⏳ Comprehensive error handling
- ⏳ Complete test coverage (85%+)