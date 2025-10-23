import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from main import app
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.models import User, Service, UserRole

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Setup and teardown test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(setup_database):
    """Create test user"""
    db = TestingSessionLocal()
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.USER
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def test_admin(setup_database):
    """Create test admin"""
    db = TestingSessionLocal()
    admin = User(
        name="Admin User",
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        role=UserRole.ADMIN
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()
    return admin


@pytest.fixture
def test_service(setup_database):
    """Create test service"""
    db = TestingSessionLocal()
    service = Service(
        title="Test Service",
        description="A test service",
        price=100.0,
        duration_minutes=60,
        is_active=True
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    db.close()
    return service


def get_token(email: str, password: str):
    """Helper to get JWT token"""
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password}
    )
    return response.json()["access_token"]


# ===== AUTH TESTS =====

def test_register_user(setup_database):
    """Test user registration"""
    response = client.post(
        "/auth/register",
        json={
            "name": "New User",
            "email": "newuser@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["name"] == "New User"
    assert data["role"] == "user"


def test_register_duplicate_email(test_user):
    """Test registration with duplicate email"""
    response = client.post(
        "/auth/register",
        json={
            "name": "Another User",
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(test_user):
    """Test successful login"""
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(test_user):
    """Test login with wrong password"""
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_login_nonexistent_user(setup_database):
    """Test login with non-existent user"""
    response = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "password123"}
    )
    assert response.status_code == 401


def test_refresh_token(test_user):
    """Test token refresh"""
    login_response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    refresh_token = login_response.json()["refresh_token"]
    
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_protected_route_without_token(setup_database):
    """Test accessing protected route without token"""
    response = client.get("/me")
    assert response.status_code == 403


def test_protected_route_with_invalid_token(setup_database):
    """Test accessing protected route with invalid token"""
    response = client.get(
        "/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


# ===== USER TESTS =====

def test_get_current_user(test_user):
    """Test getting current user profile"""
    token = get_token("test@example.com", "password123")
    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


def test_update_current_user(test_user):
    """Test updating current user"""
    token = get_token("test@example.com", "password123")
    response = client.patch(
        "/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Updated Name"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


# ===== SERVICE TESTS =====

def test_get_services(test_service):
    """Test getting all services (public)"""
    response = client.get("/services")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["title"] == "Test Service"


def test_get_service_by_id(test_service):
    """Test getting service by ID"""
    response = client.get(f"/services/{test_service.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Service"


def test_get_nonexistent_service(setup_database):
    """Test getting non-existent service"""
    response = client.get("/services/9999")
    assert response.status_code == 404


def test_create_service_as_admin(test_admin):
    """Test creating service as admin"""
    token = get_token("admin@example.com", "admin123")
    response = client.post(
        "/services",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "New Service",
            "description": "A new service",
            "price": 150.0,
            "duration_minutes": 90,
            "is_active": True
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Service"
    assert data["price"] == 150.0


def test_create_service_as_user_forbidden(test_user):
    """Test creating service as regular user (should fail)"""
    token = get_token("test@example.com", "password123")
    response = client.post(
        "/services",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "New Service",
            "description": "A new service",
            "price": 150.0,
            "duration_minutes": 90
        }
    )
    assert response.status_code == 403


def test_update_service_as_admin(test_admin, test_service):
    """Test updating service as admin"""
    token = get_token("admin@example.com", "admin123")
    response = client.patch(
        f"/services/{test_service.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"price": 200.0}
    )
    assert response.status_code == 200
    assert response.json()["price"] == 200.0


def test_delete_service_as_admin(test_admin, test_service):
    """Test deleting service as admin"""
    token = get_token("admin@example.com", "admin123")
    response = client.delete(
        f"/services/{test_service.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204


# ===== BOOKING TESTS =====

def test_create_booking(test_user, test_service):
    """Test creating a booking"""
    token = get_token("test@example.com", "password123")
    start_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
    
    response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "service_id": test_service.id,
            "start_time": start_time
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["service_id"] == test_service.id
    assert data["status"] == "pending"


def test_create_booking_past_time(test_user, test_service):
    """Test creating booking with past time (should fail)"""
    token = get_token("test@example.com", "password123")
    past_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
    
    response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "service_id": test_service.id,
            "start_time": past_time
        }
    )
    assert response.status_code == 422


def test_booking_conflict(test_user, test_service):
    """Test booking conflict detection"""
    token = get_token("test@example.com", "password123")
    start_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
    
    # Create first booking
    client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "service_id": test_service.id,
            "start_time": start_time
        }
    )
    
    # Try to create overlapping booking
    response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "service_id": test_service.id,
            "start_time": start_time
        }
    )
    assert response.status_code == 409
    assert "conflict" in response.json()["detail"].lower()


def test_get_user_bookings(test_user, test_service):
    """Test getting user's own bookings"""
    token = get_token("test@example.com", "password123")
    start_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
    
    # Create booking
    client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "service_id": test_service.id,
            "start_time": start_time
        }
    )
    
    # Get bookings
    response = client.get(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_admin_sees_all_bookings(test_user, test_admin, test_service):
    """Test admin can see all bookings"""
    user_token = get_token("test@example.com", "password123")
    admin_token = get_token("admin@example.com", "admin123")
    
    # User creates booking
    start_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
    client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "service_id": test_service.id,
            "start_time": start_time
        }
    )
    
    # Admin gets all bookings
    response = client.get(
        "/bookings",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_user_cannot_access_other_booking(test_user, test_admin, test_service):
    """Test user cannot access another user's booking"""
    admin_token = get_token("admin@example.com", "admin123")
    user_token = get_token("test@example.com", "password123")
    
    # Admin creates booking
    start_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
    booking_response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "service_id": test_service.id,
            "start_time": start_time
        }
    )
    booking_id = booking_response.json()["id"]
    
    # User tries to access admin's booking
    response = client.get(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


# ===== REVIEW TESTS =====

def test_create_review_for_completed_booking(test_user, test_service, test_admin):
    """Test creating review for completed booking"""
    user_token = get_token("test@example.com", "password123")
    admin_token = get_token("admin@example.com", "admin123")
    
    # Create and complete booking
    start_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
    booking_response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "service_id": test_service.id,
            "start_time": start_time
        }
    )
    booking_id = booking_response.json()["id"]
    
    # Admin marks booking as completed
    client.patch(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "completed"}
    )
    
    # User creates review
    response = client.post(
        "/reviews",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "booking_id": booking_id,
            "rating": 5,
            "comment": "Great service!"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 5
    assert data["comment"] == "Great service!"


def test_cannot_review_non_completed_booking(test_user, test_service):
    """Test cannot review pending booking"""
    token = get_token("test@example.com", "password123")
    
    # Create pending booking
    start_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
    booking_response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "service_id": test_service.id,
            "start_time": start_time
        }
    )
    booking_id = booking_response.json()["id"]
    
    # Try to review
    response = client.post(
        "/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "booking_id": booking_id,
            "rating": 5,
            "comment": "Great service!"
        }
    )
    assert response.status_code == 400


def test_get_service_reviews(test_service):
    """Test getting reviews for a service"""
    response = client.get(f"/services/{test_service.id}/reviews")
    assert response.status_code == 200
    assert isinstance(response.json(), list)