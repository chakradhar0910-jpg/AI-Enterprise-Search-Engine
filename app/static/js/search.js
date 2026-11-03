/**
 * AI Search Controller with Real-time Multi-Stage RAG Pipeline Progress
 */

document.addEventListener("DOMContentLoaded", () => {
  setupSearchForm();
  setupSuggestedChips();

  // If initial query exists in URL, run it automatically
  const searchInput = document.getElementById("searchQueryInput");
  if (searchInput && searchInput.value.trim()) {
    executeSearch(searchInput.value.trim());
  }
});

function setupSearchForm() {
  const form = document.getElementById("searchForm");
  const input = document.getElementById("searchQueryInput");

  if (!form || !input) return;

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (query) {
      executeSearch(query);
    }
  });
}

function setupSuggestedChips() {
  const chips = document.querySelectorAll(".chip-btn");
  const input = document.getElementById("searchQueryInput");

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const text = chip.dataset.query || chip.textContent.trim();
      if (input) {
        input.value = text;
        executeSearch(text);
      }
    });
  });
}

async function executeSearch(query) {
  const resultsContainer = document.getElementById("searchResultsArea");
  const loadingArea = document.getElementById("searchLoadingArea");
  const emptyState = document.getElementById("searchEmptyState");
  const searchBtn = document.getElementById("searchSubmitBtn");

  const modeRadios = document.getElementsByName("searchMode");
  let selectedMode = "hybrid";
  for (const r of modeRadios) {
    if (r.checked) {
      selectedMode = r.value;
      break;
    }
  }

  if (emptyState) emptyState.classList.add("d-none");
  if (resultsContainer) resultsContainer.classList.add("d-none");
  if (loadingArea) loadingArea.classList.remove("d-none");
  if (searchBtn) searchBtn.disabled = true;

  // Step-by-step progress simulation
  updatePipelineStep("step1", "active");
  setTimeout(() => updatePipelineStep("step2", "active"), 250);
  setTimeout(() => updatePipelineStep("step3", "active"), 500);

  try {
    const response = await fetch("/search/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query,
        mode: selectedMode,
        top_k: 5
      })
    });

    const data = await response.json();

    if (loadingArea) loadingArea.classList.add("d-none");
    if (searchBtn) searchBtn.disabled = false;

    if (response.ok && data.success) {
      renderSearchResults(data);
    } else {
      showToast(data.error || "Search retrieval failed.", "danger");
      if (emptyState) emptyState.classList.remove("d-none");
    }
  } catch (err) {
    if (loadingArea) loadingArea.classList.add("d-none");
    if (searchBtn) searchBtn.disabled = false;
    showToast("Network error executing search: " + err, "danger");
    if (emptyState) emptyState.classList.remove("d-none");
  }
}

function updatePipelineStep(stepId, state) {
  const el = document.getElementById(stepId);
  if (!el) return;
  if (state === "active") {
    el.classList.add("fw-bold", "text-primary");
    el.classList.remove("text-muted");
  } else {
    el.classList.remove("fw-bold", "text-primary");
    el.classList.add("text-muted");
  }
}

function renderSearchResults(data) {
  const resultsContainer = document.getElementById("searchResultsArea");
  if (!resultsContainer) return;

  resultsContainer.classList.remove("d-none");

  // Populate Query title
  const queryDisplay = document.getElementById("resultQueryTitle");
  if (queryDisplay) queryDisplay.textContent = `"${data.query}"`;

  // Populate Meta Info
  const metaDisplay = document.getElementById("resultMetaInfo");
  if (metaDisplay) {
    metaDisplay.innerHTML = `
      <span class="badge bg-light text-dark border me-1"><i class="bi bi-cpu"></i> ${data.provider} (${data.model})</span>
      <span class="badge bg-light text-dark border me-1"><i class="bi bi-funnel"></i> ${data.search_mode.toUpperCase()}</span>
      <span class="badge bg-light text-dark border"><i class="bi bi-file-earmark-check"></i> ${data.total_retrieved} Chunks Retrieved</span>
    `;
  }

  // Populate Grounded Answer Body
  const answerBody = document.getElementById("resultAnswerContent");
  if (answerBody) {
    // Format simple markdown bold and lists
    let formatted = data.answer
      .replace(/^### (.*$)/gim, '<h5 class="fw-bold mt-3 mb-2">$1</h5>')
      .replace(/^## (.*$)/gim, '<h4 class="fw-bold mt-3 mb-2">$1</h4>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/^• (.*$)/gim, '<li class="mb-2">$1</li>')
      .replace(/^\* (.*$)/gim, '<li class="mb-2">$1</li>')
      .replace(/\n\n/g, '<br><br>');

    answerBody.innerHTML = formatted;
  }

  // Setup Copy Answer Button
  const copyBtn = document.getElementById("copyAnswerBtn");
  if (copyBtn) {
    copyBtn.onclick = () => copyToClipboard(data.answer, copyBtn);
  }

  // Populate Sources List
  const sourcesContainer = document.getElementById("sourcesCardsList");
  if (sourcesContainer) {
    if (!data.sources || data.sources.length === 0) {
      sourcesContainer.innerHTML = '<p class="text-muted small">No direct source chunks retrieved.</p>';
      return;
    }

    let sourcesHtml = "";
    data.sources.forEach((src, idx) => {
      const pageStr = src.page_number ? `Page ${src.page_number}` : "Full Document";
      const sectionStr = src.section_title ? ` • ${src.section_title}` : "";
      const scoreBadge = src.relevance_percentage
        ? `<span class="badge bg-success-subtle text-success border border-success-subtle fw-semibold">${src.relevance_percentage}% Match</span>`
        : "";

      sourcesHtml += `
        <div class="source-card">
          <div class="source-header">
            <div class="source-title">
              <span class="badge bg-primary text-white me-1">[${idx + 1}]</span>
              <span>${src.document_name}</span>
              <span class="text-muted small fw-normal">(${pageStr}${sectionStr})</span>
            </div>
            <div>
              ${scoreBadge}
              <span class="badge bg-light text-muted border ms-1">${src.retrieval_method || 'Hybrid'}</span>
            </div>
          </div>
          <div class="source-snippet">
            "${src.snippet}"
          </div>
        </div>
      `;
    });

    sourcesContainer.innerHTML = sourcesHtml;
  }
}
