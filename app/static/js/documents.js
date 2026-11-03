/**
 * Document Management and Drag-and-Drop Ingestion Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  setupDropzone();
  setupDocumentFilters();
});

function setupDropzone() {
  const dropzone = document.getElementById("uploadDropzone");
  const fileInput = document.getElementById("fileInput");
  const uploadForm = document.getElementById("documentUploadForm");
  const uploadProgress = document.getElementById("uploadProgress");
  const uploadProgressBar = document.getElementById("uploadProgressBar");
  const uploadStatusText = document.getElementById("uploadStatusText");
  const uploadSubmitBtn = document.getElementById("uploadSubmitBtn");

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("click", () => fileInput.click());

  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      fileInput.files = files;
      updateSelectedFilesList(files);
    }
  });

  fileInput.addEventListener("change", () => {
    updateSelectedFilesList(fileInput.files);
  });

  if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!fileInput.files || fileInput.files.length === 0) {
        showToast("Please choose at least one document to upload.", "warning");
        return;
      }

      const formData = new FormData(uploadForm);
      uploadProgress.classList.remove("d-none");
      uploadProgressBar.style.width = "30%";
      uploadStatusText.textContent = "Uploading files and extracting text...";
      uploadSubmitBtn.disabled = true;

      try {
        uploadProgressBar.style.width = "60%";
        uploadStatusText.textContent = "Generating embeddings and indexing in FAISS...";

        const response = await fetch("/documents/api/documents/upload", {
          method: "POST",
          body: formData
        });

        const data = await response.json();
        uploadProgressBar.style.width = "100%";

        if (response.ok && data.success) {
          uploadStatusText.textContent = "Indexing complete!";
          showToast("Documents uploaded and indexed successfully!", "success");
          setTimeout(() => {
            window.location.reload();
          }, 1200);
        } else {
          showToast(data.error || "Upload failed", "danger");
          uploadSubmitBtn.disabled = false;
        }
      } catch (err) {
        showToast("Network error uploading files: " + err, "danger");
        uploadSubmitBtn.disabled = false;
      }
    });
  }
}

function updateSelectedFilesList(files) {
  const previewContainer = document.getElementById("selectedFilesPreview");
  if (!previewContainer) return;

  if (files.length === 0) {
    previewContainer.innerHTML = "";
    return;
  }

  let html = '<div class="list-group list-group-flush border rounded-3 mt-2">';
  for (let i = 0; i < files.length; i++) {
    const f = files[i];
    const sizeKb = (f.size / 1024).toFixed(1);
    html += `
      <div class="list-group-item d-flex align-items-center justify-content-between py-2">
        <div class="d-flex align-items-center gap-2 text-truncate">
          <i class="bi bi-file-earmark-text text-primary"></i>
          <span class="small fw-semibold text-truncate">${f.name}</span>
        </div>
        <span class="badge bg-light text-muted border">${sizeKb} KB</span>
      </div>
    `;
  }
  html += "</div>";
  previewContainer.innerHTML = html;
}

async function deleteDocument(docId, docName) {
  if (!confirm(`Are you sure you want to permanently delete '${docName}'? All vector embeddings will be removed from the index.`)) {
    return;
  }

  try {
    const resp = await fetch(`/documents/api/documents/${docId}`, {
      method: "DELETE"
    });
    const data = await resp.json();
    if (resp.ok && data.success) {
      showToast(data.message, "success");
      const row = document.getElementById(`doc-row-${docId}`);
      if (row) row.remove();
      setTimeout(() => window.location.reload(), 1000);
    } else {
      showToast(data.error || "Failed to delete document.", "danger");
    }
  } catch (err) {
    showToast("Error deleting document: " + err, "danger");
  }
}

async function reprocessDocument(docId) {
  showToast("Re-extracting, re-chunking, and re-indexing document...", "info");
  try {
    const resp = await fetch(`/documents/api/documents/${docId}/reprocess`, {
      method: "POST"
    });
    const data = await resp.json();
    if (resp.ok && data.success) {
      showToast(data.message, "success");
      setTimeout(() => window.location.reload(), 1000);
    } else {
      showToast(data.error || data.message || "Reprocessing failed.", "danger");
    }
  } catch (err) {
    showToast("Error reprocessing document: " + err, "danger");
  }
}

function setupDocumentFilters() {
  const searchInput = document.getElementById("docSearchFilter");
  const typeFilter = document.getElementById("docTypeFilter");
  const statusFilter = document.getElementById("docStatusFilter");

  if (!searchInput && !typeFilter && !statusFilter) return;

  function filterRows() {
    const query = (searchInput?.value || "").toLowerCase().trim();
    const selectedType = (typeFilter?.value || "").toLowerCase();
    const selectedStatus = (statusFilter?.value || "").toLowerCase();

    const rows = document.querySelectorAll(".document-table-row");
    rows.forEach((row) => {
      const name = (row.dataset.docName || "").toLowerCase();
      const type = (row.dataset.docType || "").toLowerCase();
      const status = (row.dataset.docStatus || "").toLowerCase();

      const matchesQuery = !query || name.includes(query);
      const matchesType = !selectedType || type === selectedType;
      const matchesStatus = !selectedStatus || status === selectedStatus;

      if (matchesQuery && matchesType && matchesStatus) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
    });
  }

  if (searchInput) searchInput.addEventListener("input", filterRows);
  if (typeFilter) typeFilter.addEventListener("change", filterRows);
  if (statusFilter) statusFilter.addEventListener("change", filterRows);
}
