/**
 * AI-Based Enterprise Search Engine - Core Client Utilities
 */

document.addEventListener("DOMContentLoaded", () => {
  // Initialize mobile sidebar toggle
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebar = document.querySelector(".app-sidebar");

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => {
      sidebar.classList.toggle("show");
    });

    // Close when clicking outside on mobile
    document.addEventListener("click", (e) => {
      if (window.innerWidth <= 992 && !sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove("show");
      }
    });
  }

  // Initialize Bootstrap Tooltips if available
  if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map((el) => new bootstrap.Tooltip(el));
  }
});

/**
 * Display a modern Toast notification
 * @param {string} message - Message text to display
 * @param {string} type - 'success', 'danger', 'warning', 'info'
 */
function showToast(message, type = "info") {
  let toastContainer = document.querySelector(".toast-container");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.className = "toast-container";
    document.body.appendChild(toastContainer);
  }

  const iconMap = {
    success: "bi-check-circle-fill text-success",
    danger: "bi-exclamation-triangle-fill text-danger",
    warning: "bi-exclamation-circle-fill text-warning",
    info: "bi-info-circle-fill text-info"
  };

  const toastId = "toast_" + Date.now();
  const toastHtml = `
    <div id="${toastId}" class="toast align-items-center border-0 shadow-lg" role="alert" aria-live="assertive" aria-atomic="true" style="background: #ffffff; border-radius: 10px; margin-bottom: 0.75rem;">
      <div class="d-flex p-3">
        <div class="toast-body d-flex align-items-center gap-2 text-dark font-sans" style="font-size: 0.9rem;">
          <i class="bi ${iconMap[type] || iconMap.info} fs-5"></i>
          <span>${message}</span>
        </div>
        <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    </div>
  `;

  toastContainer.insertAdjacentHTML("beforeend", toastHtml);
  const toastEl = document.getElementById(toastId);
  if (typeof bootstrap !== "undefined" && bootstrap.Toast) {
    const bsToast = new bootstrap.Toast(toastEl, { delay: 4500 });
    bsToast.show();
    toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
  } else {
    setTimeout(() => toastEl.remove(), 4500);
  }
}

/**
 * Copy text string to user clipboard with visual feedback
 */
function copyToClipboard(text, btnElement = null) {
  navigator.clipboard.writeText(text).then(() => {
    showToast("Copied to clipboard!", "success");
    if (btnElement) {
      const origHtml = btnElement.innerHTML;
      btnElement.innerHTML = '<i class="bi bi-check2"></i> Copied';
      setTimeout(() => {
        btnElement.innerHTML = origHtml;
      }, 2000);
    }
  }).catch((err) => {
    showToast("Failed to copy: " + err, "danger");
  });
}
