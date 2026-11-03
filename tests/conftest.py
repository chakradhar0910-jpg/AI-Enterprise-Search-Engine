import pytest
from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import User, Department


@pytest.fixture
def app():
    """Create test application configured with in-memory database."""
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for HTTP requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Standard user fixture."""
    with app.app_context():
        user = User.query.filter_by(email="user@enterprise.ai").first()
        if not user:
            user = User(username="testuser", email="user@enterprise.ai", role="user")
            user.set_password("User@123456")
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture
def test_admin(app):
    """Administrator user fixture."""
    with app.app_context():
        admin = User.query.filter_by(email="admin@enterprise.ai").first()
        if not admin:
            admin = User(username="adminuser", email="admin@enterprise.ai", role="admin")
            admin.set_password("Admin@123456")
            db.session.add(admin)
            db.session.commit()
        return admin
