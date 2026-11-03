import pytest
from app.models import User


def test_user_password_hashing(app):
    """Verify passwords are never stored in plain text and hashes verify accurately."""
    with app.app_context():
        user = User(username="alice", email="alice@test.com", role="user")
        user.set_password("SecurePassword!123")
        assert user.password_hash != "SecurePassword!123"
        assert user.check_password("SecurePassword!123") is True
        assert user.check_password("WrongPassword") is False


def test_user_registration(client, app):
    """Test user registration endpoint."""
    resp = client.post("/auth/register", data={
        "username": "newemployee",
        "email": "employee@enterprise.ai",
        "password": "Password@123",
        "confirm_password": "Password@123"
    }, follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        created = User.query.filter_by(username="newemployee").first()
        assert created is not None
        assert created.email == "employee@enterprise.ai"
        assert created.role == "user"


def test_user_login_success(client, test_user):
    """Test login with valid credentials."""
    resp = client.post("/auth/login", data={
        "email": "user@enterprise.ai",
        "password": "User@123456"
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Dashboard" in resp.data or b"Welcome back" in resp.data


def test_user_login_invalid_password(client, test_user):
    """Test login failure with incorrect password."""
    resp = client.post("/auth/login", data={
        "email": "user@enterprise.ai",
        "password": "IncorrectPassword"
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Invalid email or password" in resp.data


def test_protected_route_redirects(client):
    """Test that unauthorized users cannot access protected views."""
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]
