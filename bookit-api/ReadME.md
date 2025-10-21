# BookIt API - Production-Ready Booking Platform

A comprehensive REST API for managing bookings, services, and reviews built with FastAPI and PostgreSQL.

## 🚀 Live Deployment

- **Base URL**: `https://your-app.pipeops.app` (update after deployment)
- **API Documentation**: `https://your-app.pipeops.app/docs`
- **ReDoc**: `https://your-app.pipeops.app/redoc`

## 📋 Table of Contents

- [Architecture Decisions](#architecture-decisions)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Local Development](#local-development)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Deployment](#deployment)

## 🏗️ Architecture Decisions

### Database Choice: PostgreSQL

**Why PostgreSQL over MongoDB?**

1. **Data Integrity**: Bookings require ACID compliance to prevent double-bookings and ensure data consistency
2. **Complex Relationships**: Strong foreign key constraints between Users, Services, Bookings, and Reviews
3. **Transaction Support**: Critical for booking operations that need atomicity
4. **Mature Ecosystem**: Well-established tools (Alembic for migrations, pgAdmin for management)
5. **Query Performance**: Excellent support for complex queries with JOINs, crucial for filtering bookings by date ranges and status
6. **Check Constraints**: Database-level validation (e.g., rating 1-5, positive prices, valid time ranges)

### Clean Architecture

The project follows a **three-layer architecture**:

```
┌─────────────┐
│   Routers   │  ← HTTP layer (FastAPI endpoints)
├─────────────┤
│  Services   │  ← Business logic layer (future expansion)
├─────────────┤
│Repositories │  ← Data access layer (SQL queries)
└─────────────┘
```

**Benefits:**
- **Testability**: Each layer can be tested independently
- **Maintainability**: Changes to database don't affect business logic
- **Scalability**: Easy to add caching, additional data sources, or switch ORMs
- **Separation of Concerns**: HTTP concerns separate from business rules and data access

### Security Design

- **Bcrypt Password Hashing**: Industry-standard, salt-based hashing (cost factor 12)
- **JWT Authentication**: Stateless tokens with short-lived access tokens (30 min) and refresh tokens (7 days)
- **Role-Based Access Control (RBAC)**: User and Admin roles with granular permissions
- **Input Validation**: Pydantic schemas validate all inputs before reaching business logic
- **SQL Injection Prevention**: SQLAlchemy ORM parameterizes all queries

## ✨ Features

### Authentication & Authorization ✅
- User registration with email uniqueness validation
- Secure login with JWT tokens (access + refresh)
- Token refresh mechanism
- Role-based access control (User/Admin)
- Password hashing with bcrypt

### User Management ✅
- View user profile
- Update user information
- Email uniqueness enforcement

### Service Management ✅
- **Public**: Browse and search services
- **Admin Only**: Create, update, and delete services
- Filter by price range, search query, and active status
- Price and duration validation

### Booking System ✅
- Create bookings with automatic end-time calculation
- **Conflict Detection**: Prevents double-booking same service at overlapping times (409 Conflict)
- Users see only their bookings; admins see all
- Filter by status, date range
- Users can reschedule/cancel pending/confirmed bookings
- Admins can update any booking status
- Time-based deletion rules (users: before start; admins: anytime)

### Review System ✅
- Users can review only their completed bookings
- One review per booking constraint
- Public access to service reviews
- Update/delete own reviews
- Admins can delete any review
- Rating validation (1-5 stars)

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Migrations**: Alembic 1.12
- **Authentication**: JWT (python-jose) + Bcrypt (passlib)
- **Validation**: Pydantic 2.5
- **Testing**: Pytest with async support
- **Server**: Uvicorn with production settings
- **Deployment**: PipeOps (recommended)

## 📁 Project Structure

```
bookit-api/
├── alembic/                    # Database migrations
│   ├── versions/              # Migration files
│   └── env.py                 # Alembic configuration
├── app/
│   ├── api/
│   │   └── v1/               # API version 1
│   │       ├── auth.py       # Authentication endpoints
│   │       ├── users.py      # User management
│   │       ├── services.py   # Service CRUD
│   │       ├── bookings.py   # Booking management
│   │       └── reviews.py    # Review system
│   ├── core/
│   │   ├── config.py         # Settings & environment
│   │   ├── database.py       # DB connection
│   │   ├── security.py       # JWT & password hashing
│   │   └── dependencies.py   # Auth dependencies
│   ├── models/
│   │   └── models.py         # SQLAlchemy models
│   ├── repositories/         # Data access layer
│   │   ├── user_repository.py
│   │   ├── service_repository.py
│   │   ├── booking_repository.py
│   │   └── review_repository.py
│   └── schemas/
│       └── schemas.py        # Pydantic models
├── tests/
│   └── test_api.py          # Comprehensive test suite
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
├── alembic.ini              # Alembic config
├── .env.example             # Environment Template
└── README.md                # This file
```

## 🚀 Local Development

### Prerequisites

- Python 3.9+
- PostgreSQL 14+
- pip

### Setup Steps

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd bookit-api
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up PostgreSQL**
```bash
# Create database
createdb bookit_db

# Or using psql
psql -U postgres
CREATE DATABASE bookit_db;
```

5. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings and rename if necessary
```

6. **Run migrations**
```bash
alembic upgrade head
```

7. **Start the server**
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## 🔐 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | ✅ |
| `SECRET_KEY` | JWT secret key (use `openssl rand -hex 32`) | - | ✅ |
| `ALGORITHM` | JWT algorithm | HS256 | ❌ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | 30 | ❌ |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | 7 | ❌ |
| `DEBUG` | Enable debug mode | False | ❌ |
| `ALLOWED_ORIGINS` | CORS origins | ["*"] | ❌ |

### Example `.env` file

```env
DATABASE_URL=postgresql://user:password@localhost:5432/bookit_db
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DEBUG=False
ALLOWED_ORIGINS=["*"]
```

## 📡 API Endpoints

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Register new user | ❌ |
| POST | `/auth/login` | Login and get tokens | ❌ |
| POST | `/auth/refresh` | Refresh access token | ❌ |
| POST | `/auth/logout` | Logout (client-side) | ❌ |

### Users

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/me` | Get current user profile | ✅ User |
| PATCH | `/me` | Update current user | ✅ User |

### Services

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/services` | List services (with filters) | ❌ |
| GET | `/services/{id}` | Get service details | ❌ |
| POST | `/services` | Create service | ✅ Admin |
| PATCH | `/services/{id}` | Update service | ✅ Admin |
| DELETE | `/services/{id}` | Delete service | ✅ Admin |
| GET | `/services/{id}/reviews` | Get service reviews | ❌ |

### Bookings

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/bookings` | Create booking | ✅ User |
| GET | `/bookings` | List bookings (filtered) | ✅ User/Admin |
| GET | `/bookings/{id}` | Get booking details | ✅ Owner/Admin |
| PATCH | `/bookings/{id}` | Update booking | ✅ Owner/Admin |
| DELETE | `/bookings/{id}` | Delete booking | ✅ Owner/Admin |

### Reviews

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/reviews` | Create review | ✅ User |
| GET | `/reviews/{id}` | Get review | ❌ |
| PATCH | `/reviews/{id}` | Update review | ✅ Owner |
| DELETE | `/reviews/{id}` | Delete review | ✅ Owner/Admin |

### HTTP Status Codes Used

- **200 OK**: Successful GET, PATCH
- **201 Created**: Successful POST (resource created)
- **204 No Content**: Successful DELETE
- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Valid auth but insufficient permissions
- **404 Not Found**: Resource doesn't exist
- **409 Conflict**: Booking time slot conflict
- **422 Unprocessable Entity**: Validation error

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v
```

### Test Coverage

The test suite includes:
- ✅ Authentication flow (register, login, refresh, logout)
- ✅ Authorization checks (401, 403 responses)
- ✅ User CRUD operations
- ✅ Service management (public access & admin-only)
- ✅ Booking creation with conflict detection (409)
- ✅ Booking permissions (users vs admins)
- ✅ Review creation rules (completed bookings only)
- ✅ One review per booking constraint
- ✅ Happy and unhappy paths
- ✅ Proper status code assertions

## 🌐 Deployment

### PipeOps Deployment

1. **Prerequisites**
   - PipeOps account
   - Git repository (GitHub/GitLab)
   - PostgreSQL database (PipeOps provides managed databases)

2. **Deployment Steps**

```bash
# 1. Push code to Git repository
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main

# 2. Connect to PipeOps
# - Log in to PipeOps dashboard
# - Create new project
# - Connect your Git repository
# - Select Python/FastAPI template

# 3. Configure environment variables in PipeOps dashboard
DATABASE_URL=<provided-by-pipeops>
SECRET_KEY=<generate-secure-key>
# ... other env vars

# 4. Add build configuration
# PipeOps will auto-detect requirements.txt and create:
# - Build command: pip install -r requirements.txt
# - Start command: uvicorn main:app --host 0.0.0.0 --port 8000

# 5. Run migrations after deployment
# SSH into server or use PipeOps console:
alembic upgrade head

# 6. Create admin user (optional - via API or database)
```

3. **Production Checklist**

- ✅ Set strong `SECRET_KEY` (use `openssl rand -hex 32`)
- ✅ Set `DEBUG=False`
- ✅ Configure `ALLOWED_ORIGINS` for your frontend domain
- ✅ Use managed PostgreSQL database with SSL
- ✅ Enable HTTPS (PipeOps provides this)
- ✅ Set up database backups
- ✅ Configure monitoring and logs
- ✅ Run database migrations
- ✅ Test all endpoints in production

### Alternative Deployment Options

#### Render

```yaml
# render.yaml
services:
  - type: web
    name: bookit-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: bookit-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: PYTHON_VERSION
        value: 3.11.0

databases:
  - name: bookit-db
    databaseName: bookit
    user: bookit
```

#### Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/bookit
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db

  db:
    image: postgres:14
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=bookit
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 📊 Database Schema

```sql
-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Services Table
CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description VARCHAR(1000) NOT NULL,
    price FLOAT NOT NULL CHECK (price >= 0),
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bookings Table
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    service_id INTEGER REFERENCES services(id) ON DELETE CASCADE,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL CHECK (end_time > start_time),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reviews Table
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER UNIQUE REFERENCES bookings(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment VARCHAR(1000) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_services_active ON services(is_active);
CREATE INDEX idx_bookings_user ON bookings(user_id);
CREATE INDEX idx_bookings_service ON bookings(service_id);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_time ON bookings(start_time, end_time);
```

## 🔍 Key Features Explained

### 1. Booking Conflict Prevention

The system prevents double-booking through database-level checks:

```python
# Checks for overlapping time slots
def check_conflict(service_id, start_time, end_time):
    # Returns True if conflict exists
    # Considers only PENDING and CONFIRMED bookings
    # Excludes CANCELLED and COMPLETED bookings
```

**Conflict scenarios handled:**
- Same service booked at exact same time
- New booking starts during existing booking
- New booking ends during existing booking
- New booking completely contains existing booking

Returns **409 Conflict** when conflict detected.

### 2. Role-Based Access Control

**User Permissions:**
- ✅ Create/view/update/delete own bookings
- ✅ Create/update/delete own reviews
- ✅ View own profile
- ❌ Cannot access other users' data
- ❌ Cannot manage services

**Admin Permissions:**
- ✅ All user permissions
- ✅ Create/update/delete services
- ✅ View all bookings
- ✅ Update any booking status
- ✅ Delete any review

### 3. Review Rules

- Must be for a **completed** booking
- User must **own** the booking
- **One review per booking** (enforced by unique constraint)
- Rating must be **1-5 stars**
- Comment required (1-1000 characters)

### 4. JWT Token Strategy

**Access Token (30 minutes):**
- Used for API authentication
- Short-lived for security
- Contains user ID and type

**Refresh Token (7 days):**
- Used to get new access tokens
- Longer-lived for convenience
- Single-use recommended (not implemented for simplicity)

**Security considerations:**
- Tokens are stateless (no database storage)
- For production: consider token blacklisting for logout
- Store tokens securely on client (httpOnly cookies recommended)

## 🎯 Usage Examples

### 1. Register and Login

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword123"
  }'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepassword123"
  }'

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Create Booking

```bash
# Create booking (requires authentication)
curl -X POST http://localhost:8000/bookings \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_id": 1,
    "start_time": "2025-10-25T14:00:00"
  }'

# Response (201 Created):
{
  "id": 1,
  "user_id": 1,
  "service_id": 1,
  "start_time": "2025-10-25T14:00:00",
  "end_time": "2025-10-25T15:00:00",
  "status": "pending",
  "created_at": "2025-10-21T10:30:00"
}
```

### 3. Handle Booking Conflict

```bash
# Try to book same time slot
curl -X POST http://localhost:8000/bookings \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_id": 1,
    "start_time": "2025-10-25T14:00:00"
  }'

# Response (409 Conflict):
{
  "detail": "Booking conflict: time slot is not available"
}
```

### 4. Create Review (Admin marks booking complete first)

```bash
# Admin updates booking status
curl -X PATCH http://localhost:8000/bookings/1 \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'

# User creates review
curl -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer USER_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": 1,
    "rating": 5,
    "comment": "Excellent service, highly recommended!"
  }'
```

## 🐛 Troubleshooting

### Common Issues

**1. Database Connection Error**
```
sqlalchemy.exc.OperationalError: connection refused
```
Solution: Check `DATABASE_URL` in `.env` and ensure PostgreSQL is running.

**2. Migration Conflicts**
```
alembic.util.exc.CommandError: Target database is not up to date
```
Solution:
```bash
alembic stamp head
alembic revision --autogenerate -m "fix"
alembic upgrade head
```

**3. 401 Unauthorized**
```
{"detail": "Invalid authentication credentials"}
```
Solution: Check token format in header: `Authorization: Bearer <token>`

**4. 409 Conflict on Booking**
```
{"detail": "Booking conflict: time slot is not available"}
```
Solution: Choose different time slot or check existing bookings.

## 📈 Performance Considerations

### Database Optimization

1. **Indexes**: Added on frequently queried columns (email, service_id, status, dates)
2. **Connection Pooling**: Configured for 5 connections with 10 overflow
3. **Query Optimization**: Repository pattern allows easy query optimization

### Scaling Strategies

1. **Horizontal Scaling**: Stateless JWT enables multiple API instances
2. **Caching**: Add Redis for frequently accessed services
3. **Database**: PostgreSQL read replicas for read-heavy operations
4. **CDN**: Static content delivery (if serving files)

## 🔒 Security Best Practices

- ✅ Passwords hashed with bcrypt (cost factor 12)
- ✅ JWT tokens with expiration
- ✅ HTTPS in production (via PipeOps)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Input validation (Pydantic)
- ✅ CORS configuration
- ✅ Rate limiting (recommended: add middleware)
- ✅ Secrets in environment variables

## 📝 Future Enhancements

- [ ] Email notifications for bookings
- [ ] Payment integration (Stripe/PayPal)
- [ ] Service availability calendar
- [ ] Booking reminders
- [ ] User avatar uploads
- [ ] Service categories and tags
- [ ] Advanced search with Elasticsearch
- [ ] Rate limiting middleware
- [ ] API versioning strategy
- [ ] WebSocket for real-time updates
- [ ] Admin dashboard
- [ ] Analytics and reporting

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Support

For issues and questions:
- Create an issue on GitHub
- Email: support@bookit.example.com
- Documentation: Check `/docs` endpoint

## 🙏 Acknowledgments

- FastAPI for the excellent framework
- SQLAlchemy for robust ORM
- Alembic for seamless migrations
- PipeOps for easy deployment

---

**Built with ❤️ using FastAPI and PostgreSQL**