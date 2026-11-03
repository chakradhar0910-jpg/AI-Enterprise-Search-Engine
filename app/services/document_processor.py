import os
import shutil
from pathlib import Path
from typing import Tuple, Dict, Any, List
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Document, DocumentChunk, DocumentPermission
from app.services.text_extractor import TextExtractor, ExtractionError
from app.services.text_chunker import TextChunker
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.keyword_search import KeywordSearchService


class DocumentProcessor:
    """Manages the full lifecycle of document ingestion, text extraction, chunking, embedding, and vector indexing."""

    def __init__(self, upload_folder: str = "data/uploads", processed_folder: str = "data/processed"):
        self.upload_folder = Path(upload_folder)
        self.processed_folder = Path(processed_folder)
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        self.processed_folder.mkdir(parents=True, exist_ok=True)

        self.chunker = TextChunker()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.keyword_service = KeywordSearchService()

    def process_document(self, document_id: int) -> Tuple[bool, str]:
        """
        Execute full extraction and indexing pipeline for a Document record.
        Returns (success: bool, message: str).
        """
        doc = Document.query.get(document_id)
        if not doc:
            return False, f"Document ID {document_id} not found."

        try:
            doc.processing_status = "Processing"
            doc.indexing_status = "Pending"
            doc.error_message = None
            db.session.commit()

            file_path = Path(doc.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found on disk: {doc.file_path}")

            # 1. Extract text and structural pages
            extracted_sections = TextExtractor.extract(str(file_path), doc.file_type)
            if not extracted_sections:
                raise ExtractionError("No content extracted from document.")

            # Calculate total pages
            page_numbers = [s["page_number"] for s in extracted_sections if s["page_number"]]
            doc.page_count = max(page_numbers) if page_numbers else 1

            # 2. Split into overlapping chunks
            chunks_data = self.chunker.chunk_extracted_sections(extracted_sections)
            if not chunks_data:
                raise ExtractionError("Document produced 0 text chunks after processing.")

            # Clean any existing chunks if reprocessing
            DocumentChunk.query.filter_by(document_id=doc.id).delete()
            self.vector_store.remove_document_vectors(doc.id)
            self.keyword_service.remove_document(doc.id)
            db.session.flush()

            # 3. Save chunks in database
            db_chunks = []
            chunk_texts = []
            for item in chunks_data:
                chunk_obj = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=item["chunk_index"],
                    chunk_text=item["chunk_text"],
                    page_number=item["page_number"],
                    section_title=item["section_title"],
                    token_count=item["token_count"]
                )
                db.session.add(chunk_obj)
                db_chunks.append(chunk_obj)
                chunk_texts.append(item["chunk_text"])

            db.session.commit()

            # 4. Generate dense embeddings using SentenceTransformers
            embeddings = self.embedding_service.encode(chunk_texts)

            # 5. Index in FAISS
            chunks_meta = []
            bm25_items = []
            for i, chunk_obj in enumerate(db_chunks):
                chunks_meta.append({
                    "chunk_id": chunk_obj.id,
                    "document_id": doc.id,
                    "department_id": doc.department_id,
                    "page_number": chunk_obj.page_number,
                    "section_title": chunk_obj.section_title
                })
                bm25_items.append({
                    "chunk_id": chunk_obj.id,
                    "document_id": doc.id,
                    "chunk_text": chunk_obj.chunk_text
                })

            faiss_ids = self.vector_store.add_vectors(embeddings, chunks_meta)

            # Update embedding_id on chunks
            for i, fid in enumerate(faiss_ids):
                db_chunks[i].embedding_id = fid

            # 6. Index in BM25
            self.keyword_service.add_chunks(bm25_items)

            # 7. Update document status
            doc.processing_status = "Indexed"
            doc.indexing_status = "Indexed"
            doc.chunk_count = len(db_chunks)

            # Generate short document summary from first 2 chunks
            summary_preview = " ".join([c.chunk_text for c in db_chunks[:2]])
            doc.summary = summary_preview[:350] + ("..." if len(summary_preview) > 350 else "")

            db.session.commit()
            return True, f"Successfully processed and indexed {len(db_chunks)} chunks for '{doc.original_filename}'."

        except Exception as e:
            db.session.rollback()
            doc.processing_status = "Failed"
            doc.indexing_status = "Failed"
            doc.error_message = str(e)
            db.session.commit()
            print(f"[DocumentProcessor] Ingestion failed for document {doc.id}: {e}")
            return False, f"Ingestion failed: {str(e)}"

    def delete_document(self, document_id: int) -> Tuple[bool, str]:
        """Delete document file, database records, vector index entries, and BM25 entries."""
        doc = Document.query.get(document_id)
        if not doc:
            return False, "Document not found."

        try:
            # 1. Remove vectors from FAISS
            self.vector_store.remove_document_vectors(doc.id)

            # 2. Remove entries from BM25
            self.keyword_service.remove_document(doc.id)

            # 3. Remove physical file
            file_path = Path(doc.file_path)
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception as fe:
                    print(f"[DocumentProcessor] Warning deleting file {file_path}: {fe}")

            # 4. Remove database records (cascades to chunks and permissions)
            db.session.delete(doc)
            db.session.commit()
            return True, f"Document '{doc.original_filename}' and its vector embeddings deleted successfully."
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to delete document: {str(e)}"
