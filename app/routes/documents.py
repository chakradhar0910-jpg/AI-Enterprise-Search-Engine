import os
import uuid
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Document, DocumentChunk, Department, DocumentPermission
from app.services.document_processor import DocumentProcessor

documents_bp = Blueprint("documents", __name__)


def allowed_file(filename: str) -> bool:
    """Check if file has an authorized enterprise extension."""
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"pdf", "docx", "txt"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


@documents_bp.route("/")
@login_required
def documents_view():
    """Document repository and management interface."""
    # Departments list for upload modal
    departments = Department.query.order_by(Department.name.asc()).all()

    # Query documents with role-based scoping
    if current_user.is_admin:
        docs = Document.query.order_by(Document.created_at.desc()).all()
    else:
        user_dept = current_user.department_id
        docs = Document.query.filter(
            (Document.uploaded_by == current_user.id) |
            (Document.department_id == user_dept) |
            (Document.department_id.is_(None))
        ).order_by(Document.created_at.desc()).all()

    return render_template("documents.html", documents=docs, departments=departments)


@documents_bp.route("/<int:doc_id>/preview")
@login_required
def preview_document(doc_id: int):
    """Inspect document metadata and chunked passages."""
    doc = Document.query.get_or_404(doc_id)

    # Permission check
    if not current_user.is_admin and doc.uploaded_by != current_user.id:
        if doc.department_id and doc.department_id != current_user.department_id:
            flash("You do not have permission to view this document.", "danger")
            return redirect(url_for("documents.documents_view"))

    chunks = doc.chunks.order_by(DocumentChunk.chunk_index.asc()).all()
    return render_template("preview.html", document=doc, chunks=chunks)


# JSON APIs
@documents_bp.route("/api/documents/upload", methods=["POST"])
@login_required
def api_upload_document():
    """Upload one or multiple enterprise documents and trigger automated indexing pipeline."""
    if "files" not in request.files and "file" not in request.files:
        return jsonify({"success": False, "error": "No file payload found in request."}), 400

    uploaded_files = request.files.getlist("files") or [request.files["file"]]
    department_id_str = request.form.get("department_id")
    department_id = int(department_id_str) if department_id_str and department_id_str.isdigit() else current_user.department_id

    is_public = request.form.get("is_public", "false").lower() in ("true", "1", "yes")

    processor = DocumentProcessor(
        upload_folder=current_app.config["UPLOAD_FOLDER"],
        processed_folder=current_app.config["PROCESSED_FOLDER"]
    )

    results = []
    for file_obj in uploaded_files:
        if not file_obj or file_obj.filename == "":
            continue

        raw_filename = secure_filename(file_obj.filename)
        if not raw_filename or not allowed_file(raw_filename):
            results.append({
                "filename": file_obj.filename,
                "success": False,
                "error": "Unsupported file format. Please upload PDF, DOCX, or TXT."
            })
            continue

        file_ext = raw_filename.rsplit(".", 1)[1].lower()
        unique_prefix = uuid.uuid4().hex[:8]
        stored_filename = f"{unique_prefix}_{raw_filename}"
        dest_path = Path(current_app.config["UPLOAD_FOLDER"]) / stored_filename

        # Save to disk
        file_obj.save(str(dest_path))
        file_size = dest_path.stat().st_size

        # Create database record
        doc = Document(
            filename=stored_filename,
            original_filename=raw_filename,
            file_type=file_ext,
            file_path=str(dest_path),
            file_size=file_size,
            uploaded_by=current_user.id,
            department_id=department_id,
            processing_status="Uploaded",
            indexing_status="Pending"
        )
        db.session.add(doc)
        db.session.commit()

        # Add explicit permission if specified
        if is_public:
            perm = DocumentPermission(document_id=doc.id, is_public=True)
            db.session.add(perm)
            db.session.commit()

        # Execute processing pipeline
        success, msg = processor.process_document(doc.id)

        results.append({
            "id": doc.id,
            "filename": doc.original_filename,
            "success": success,
            "message": msg,
            "chunk_count": doc.chunk_count,
            "page_count": doc.page_count
        })

    return jsonify({"success": True, "results": results})


@documents_bp.route("/api/documents", methods=["GET"])
@login_required
def api_list_documents():
    """Retrieve list of documents filtered by query params."""
    status_filter = request.args.get("status")
    type_filter = request.args.get("type")

    query = Document.query
    if not current_user.is_admin:
        query = query.filter(
            (Document.uploaded_by == current_user.id) |
            (Document.department_id == current_user.department_id) |
            (Document.department_id.is_(None))
        )

    if status_filter:
        query = query.filter_by(indexing_status=status_filter)
    if type_filter:
        query = query.filter_by(file_type=type_filter.lower())

    docs = query.order_by(Document.created_at.desc()).all()
    return jsonify({"success": True, "documents": [d.to_dict() for d in docs]})


@documents_bp.route("/api/documents/<int:doc_id>", methods=["DELETE"])
@login_required
def api_delete_document(doc_id: int):
    """Delete document and purge vectors from index."""
    doc = Document.query.get_or_404(doc_id)

    # Permission check: admin or document owner
    if not current_user.is_admin and doc.uploaded_by != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized to delete this document."}), 403

    processor = DocumentProcessor(
        upload_folder=current_app.config["UPLOAD_FOLDER"],
        processed_folder=current_app.config["PROCESSED_FOLDER"]
    )
    success, msg = processor.delete_document(doc_id)

    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "error": msg}), 500


@documents_bp.route("/api/documents/<int:doc_id>/reprocess", methods=["POST"])
@login_required
def api_reprocess_document(doc_id: int):
    """Trigger re-extraction, re-chunking, and re-indexing."""
    doc = Document.query.get_or_404(doc_id)

    if not current_user.is_admin and doc.uploaded_by != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized to reprocess this document."}), 403

    processor = DocumentProcessor(
        upload_folder=current_app.config["UPLOAD_FOLDER"],
        processed_folder=current_app.config["PROCESSED_FOLDER"]
    )
    success, msg = processor.process_document(doc_id)

    return jsonify({"success": success, "message": msg})
