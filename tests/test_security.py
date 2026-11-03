import pytest
from flask_login import login_user
from app.models import User, Department, Document, DocumentPermission
from app.services.hybrid_retrieval import HybridRetriever
from app.extensions import db


def test_permission_aware_document_retrieval(app):
    """Verify regular users cannot retrieve confidential documents belonging to other departments."""
    with app.app_context():
        # Create 2 departments
        hr_dept = Department(name="HR Dept")
        legal_dept = Department(name="Legal Dept")
        db.session.add_all([hr_dept, legal_dept])
        db.session.commit()

        # Create 2 users
        hr_user = User(username="hr_user", email="hr@test.com", role="user", department_id=hr_dept.id)
        hr_user.set_password("HrPass123!")
        legal_user = User(username="legal_user", email="legal@test.com", role="user", department_id=legal_dept.id)
        legal_user.set_password("LegalPass123!")
        admin_user = User(username="admin_sec", email="admin_sec@test.com", role="admin")
        admin_user.set_password("AdminPass123!")
        db.session.add_all([hr_user, legal_user, admin_user])
        db.session.commit()

        import uuid
        # Create confidential document in Legal
        legal_doc = Document(
            filename=f"confidential_contract_{uuid.uuid4().hex[:6]}.pdf",
            original_filename="Confidential Merger NDA.pdf",
            file_type="pdf",
            file_path="dummy.pdf",
            file_size=1024,
            uploaded_by=legal_user.id,
            department_id=legal_dept.id,
            processing_status="Indexed",
            indexing_status="Indexed"
        )
        db.session.add(legal_doc)
        db.session.commit()

        # Check authorized IDs for HR user
        hr_allowed = HybridRetriever.get_authorized_document_ids(hr_user)
        assert legal_doc.id not in hr_allowed, "Security violation: HR user was able to access confidential Legal document!"

        # Check authorized IDs for Legal user
        legal_allowed = HybridRetriever.get_authorized_document_ids(legal_user)
        assert legal_doc.id in legal_allowed

        # Check authorized IDs for Admin user
        admin_allowed = HybridRetriever.get_authorized_document_ids(admin_user)
        assert legal_doc.id in admin_allowed


def test_admin_route_security_enforcement(client, test_user, test_admin):
    """Verify regular users cannot access administrative endpoints (returns 403)."""
    # 1. Login as regular user
    client.post("/auth/login", data={
        "email": test_user.email,
        "password": "User@123456"
    })

    # Try accessing admin console
    resp = client.get("/admin/")
    assert resp.status_code == 403, f"Expected 403 Forbidden for regular user, got {resp.status_code}"

    # 2. Login as admin
    client.get("/auth/logout")
    client.post("/auth/login", data={
        "email": test_admin.email,
        "password": "Admin@123456"
    })

    resp_admin = client.get("/admin/")
    assert resp_admin.status_code == 200
