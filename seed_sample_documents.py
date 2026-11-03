import os
import shutil
import uuid
from pathlib import Path
from app import create_app
from app.extensions import db
from app.models import User, Department, Document, DocumentPermission
from app.services.document_processor import DocumentProcessor

def seed_documents():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            print("No admin user found. Creating admin...")
            admin = User(username="admin", email="admin@enterprise.ai", role="admin")
            admin.set_password("Admin@123456")
            db.session.add(admin)
            db.session.commit()

        hr_dept = Department.query.filter_by(name="Human Resources").first()
        eng_dept = Department.query.filter_by(name="Engineering & Technology").first()

        sample_dir = Path(__file__).resolve().parent / "sample_documents"
        sample_files = [
            ("Employee_Leave_Policy.docx", "docx", hr_dept.id if hr_dept else None),
            ("Enterprise_Security_Guidelines.txt", "txt", eng_dept.id if eng_dept else None),
            ("Project_Apollo_Architecture.txt", "txt", eng_dept.id if eng_dept else None),
            ("Corporate_Travel_Policy.pdf", "pdf", None)
        ]

        processor = DocumentProcessor(
            upload_folder=app.config["UPLOAD_FOLDER"],
            processed_folder=app.config["PROCESSED_FOLDER"]
        )

        for filename, ftype, dept_id in sample_files:
            src_file = sample_dir / filename
            if not src_file.exists():
                print(f"File not found: {src_file}")
                continue

            # Check if document already exists
            existing = Document.query.filter_by(original_filename=filename).first()
            if existing and existing.indexing_status == "Indexed":
                print(f"Document '{filename}' already indexed (ID: {existing.id}).")
                continue

            unique_prefix = uuid.uuid4().hex[:8]
            dest_name = f"{unique_prefix}_{filename}"
            dest_path = Path(app.config["UPLOAD_FOLDER"]) / dest_name

            shutil.copy2(src_file, dest_path)
            file_size = dest_path.stat().st_size

            doc = Document(
                filename=dest_name,
                original_filename=filename,
                file_type=ftype,
                file_path=str(dest_path),
                file_size=file_size,
                uploaded_by=admin.id,
                department_id=dept_id,
                processing_status="Uploaded",
                indexing_status="Pending"
            )
            db.session.add(doc)
            db.session.commit()

            # Add public permission so all members can search
            perm = DocumentPermission(document_id=doc.id, is_public=True)
            db.session.add(perm)
            db.session.commit()

            # Run processing pipeline
            success, msg = processor.process_document(doc.id)
            print(f"[{'SUCCESS' if success else 'FAILED'}] {filename}: {msg}")

if __name__ == "__main__":
    seed_documents()
