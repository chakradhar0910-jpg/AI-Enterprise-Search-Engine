/**
 * Conversational RAG Assistant Chat Controller
 */

let activeConversationId = null;

document.addEventListener("DOMContentLoaded", () => {
  setupNewChatButton();
  setupChatInput();

  // If conversation items exist, select the first one or create new
  const firstThread = document.querySelector(".chat-thread-item");
  if (firstThread) {
    const convId = firstThread.dataset.convId;
    loadConversation(convId);
  }
});

function setupNewChatButton() {
  const newChatBtn = document.getElementById("newChatBtn");
  if (newChatBtn) {
    newChatBtn.addEventListener("click", createNewConversation);
  }
}

async function createNewConversation() {
  try {
    const resp = await fetch("/chat/api/chat/conversations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "New Enterprise Chat" })
    });
    const data = await resp.json();
    if (resp.ok && data.success) {
      prependThreadToSidebar(data.conversation);
      loadConversation(data.conversation.id);
    } else {
      showToast(data.error || "Failed to create conversation.", "danger");
    }
  } catch (err) {
    showToast("Error creating conversation: " + err, "danger");
  }
}

function prependThreadToSidebar(conv) {
  const list = document.querySelector(".chat-threads-list");
  if (!list) return;

  const itemHtml = `
    <div class="chat-thread-item active" id="thread-item-${conv.id}" data-conv-id="${conv.id}" onclick="loadConversation('${conv.id}')">
      <i class="bi bi-chat-left-text me-2 text-primary"></i>
      <span class="thread-title">${conv.title}</span>
      <button class="thread-delete-btn" onclick="event.stopPropagation(); deleteConversation('${conv.id}')" title="Delete conversation">
        <i class="bi bi-trash"></i>
      </button>
    </div>
  `;
  document.querySelectorAll(".chat-thread-item").forEach((el) => el.classList.remove("active"));
  list.insertAdjacentHTML("afterbegin", itemHtml);
}

async function loadConversation(convId) {
  activeConversationId = convId;

  // Highlight active thread item
  document.querySelectorAll(".chat-thread-item").forEach((el) => {
    if (el.dataset.convId === convId) {
      el.classList.add("active");
    } else {
      el.classList.remove("active");
    }
  });

  const messagesContainer = document.getElementById("chatMessagesArea");
  if (!messagesContainer) return;

  messagesContainer.innerHTML = '<div class="text-center py-5 text-muted"><div class="spinner-border spinner-border-sm text-primary me-2"></div> Loading conversation...</div>';

  try {
    const resp = await fetch(`/chat/api/chat/conversations/${convId}`);
    const data = await resp.json();

    if (resp.ok && data.success) {
      const conv = data.conversation;
      renderMessages(conv.messages || []);
      const titleDisplay = document.getElementById("activeChatTitle");
      if (titleDisplay) titleDisplay.textContent = conv.title;
    } else {
      messagesContainer.innerHTML = '<div class="text-center py-4 text-danger">Failed to load conversation.</div>';
    }
  } catch (err) {
    messagesContainer.innerHTML = `<div class="text-center py-4 text-danger">Error: ${err}</div>`;
  }
}

function renderMessages(messages) {
  const container = document.getElementById("chatMessagesArea");
  if (!container) return;

  if (messages.length === 0) {
    container.innerHTML = `
      <div class="text-center py-5">
        <div class="avatar-assistant mx-auto mb-3" style="width: 56px; height: 56px; font-size: 1.6rem; border-radius: 50%;">
          <i class="bi bi-robot"></i>
        </div>
        <h5 class="fw-bold text-dark">Enterprise AI Assistant</h5>
        <p class="text-muted small max-w-md mx-auto" style="max-width: 480px;">
          Ask any question regarding your enterprise policies, project documentation, or technical manuals. Every answer is grounded directly in uploaded documents with traceable source citations.
        </p>
      </div>
    `;
    return;
  }

  let html = "";
  messages.forEach((msg) => {
    html += buildMessageRow(msg.role, msg.content, msg.sources);
  });
  container.innerHTML = html;
  scrollToBottom();
}

function buildMessageRow(role, content, sources) {
  const isUser = role === "user";
  const avatarClass = isUser ? "avatar-user" : "avatar-assistant";
  const icon = isUser ? '<i class="bi bi-person-fill"></i>' : '<i class="bi bi-robot"></i>';

  let formattedContent = content
    .replace(/^### (.*$)/gim, '<h6 class="fw-bold mt-2 mb-1">$1</h6>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^• (.*$)/gim, '<li class="small mb-1">$1</li>')
    .replace(/\n/g, '<br>');

  let sourcesHtml = "";
  if (!isUser && sources && sources.length > 0) {
    let pills = "";
    sources.forEach((s, idx) => {
      const pageInfo = s.page_number ? ` (Page ${s.page_number})` : "";
      pills += `
        <div class="source-item-pill">
          <div class="d-flex align-items-center justify-content-between mb-1">
            <span class="fw-bold text-primary">[${idx + 1}] ${s.document_name}${pageInfo}</span>
            <span class="badge bg-light text-muted border">${s.relevance_percentage || 85}% match</span>
          </div>
          <div class="text-muted" style="font-size: 0.78rem;">"${s.snippet}"</div>
        </div>
      `;
    });

    const collapseId = "src_" + Math.random().toString(36).substring(2, 9);
    sourcesHtml = `
      <div class="message-sources">
        <button class="sources-toggle" type="button" data-bs-toggle="collapse" data-bs-target="#${collapseId}">
          <i class="bi bi-journal-text"></i> ${sources.length} Grounded Source Reference(s)
          <i class="bi bi-chevron-down ms-1" style="font-size: 0.7rem;"></i>
        </button>
        <div class="collapse mt-2" id="${collapseId}">
          <div class="sources-pill-list">
            ${pills}
          </div>
        </div>
      </div>
    `;
  }

  return `
    <div class="message-row ${role}">
      <div class="message-avatar ${avatarClass}">${icon}</div>
      <div class="message-bubble">
        ${formattedContent}
        ${sourcesHtml}
      </div>
    </div>
  `;
}

function setupChatInput() {
  const input = document.getElementById("chatMessageInput");
  const sendBtn = document.getElementById("sendMessageBtn");

  if (!input || !sendBtn) return;

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  sendBtn.addEventListener("click", () => {
    sendMessage();
  });
}

async function sendMessage() {
  const input = document.getElementById("chatMessageInput");
  const sendBtn = document.getElementById("sendMessageBtn");
  const messagesContainer = document.getElementById("chatMessagesArea");

  if (!input || !activeConversationId) return;
  const text = input.value.trim();
  if (!text) return;

  // Clear input
  input.value = "";
  sendBtn.disabled = true;

  // Append user message immediately
  messagesContainer.insertAdjacentHTML("beforeend", buildMessageRow("user", text, []));
  scrollToBottom();

  // Append typing indicator
  const typingId = "typing_" + Date.now();
  const typingHtml = `
    <div id="${typingId}" class="message-row assistant">
      <div class="message-avatar avatar-assistant"><i class="bi bi-robot"></i></div>
      <div class="message-bubble">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    </div>
  `;
  messagesContainer.insertAdjacentHTML("beforeend", typingHtml);
  scrollToBottom();

  try {
    const resp = await fetch(`/chat/api/chat/conversations/${activeConversationId}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    const data = await resp.json();

    // Remove typing indicator
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();
    sendBtn.disabled = false;

    if (resp.ok && data.success) {
      const assistantMsg = data.assistant_message;
      messagesContainer.insertAdjacentHTML(
        "beforeend",
        buildMessageRow("assistant", assistantMsg.content, data.sources)
      );
      scrollToBottom();
    } else {
      showToast(data.error || "Failed to generate answer.", "danger");
    }
  } catch (err) {
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();
    sendBtn.disabled = false;
    showToast("Network error in chat: " + err, "danger");
  }
}

async function deleteConversation(convId) {
  if (!confirm("Are you sure you want to delete this chat thread?")) return;

  try {
    const resp = await fetch(`/chat/api/chat/conversations/${convId}`, { method: "DELETE" });
    const data = await resp.json();
    if (resp.ok && data.success) {
      showToast("Conversation deleted.", "success");
      const item = document.getElementById(`thread-item-${convId}`);
      if (item) item.remove();

      // Load next available or reset
      const nextThread = document.querySelector(".chat-thread-item");
      if (nextThread) {
        loadConversation(nextThread.dataset.convId);
      } else {
        createNewConversation();
      }
    }
  } catch (err) {
    showToast("Error deleting conversation: " + err, "danger");
  }
}

function scrollToBottom() {
  const container = document.getElementById("chatMessagesArea");
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}
