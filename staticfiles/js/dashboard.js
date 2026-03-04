const state = {
  access: localStorage.getItem("bud_access") || "",
  refresh: localStorage.getItem("bud_refresh") || "",
};

function clearSession() {
  state.access = "";
  state.refresh = "";
  localStorage.removeItem("bud_access");
  localStorage.removeItem("bud_refresh");
}

async function request(path, options = {}, withAuth = false) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (withAuth && state.access) {
    headers.Authorization = `Bearer ${state.access}`;
  }
  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail || data.error || JSON.stringify(data);
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return data;
}

// --- Helpers ---
function getInitials(profile) {
  if (profile.first_name && profile.last_name) {
    return (profile.first_name[0] + profile.last_name[0]).toUpperCase();
  }
  if (profile.username) return profile.username.substring(0, 2).toUpperCase();
  if (profile.email) return profile.email.substring(0, 2).toUpperCase();
  return "?";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str || "";
  return div.innerHTML;
}

function formatDate(dateStr) {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric", month: "long", day: "numeric",
  });
}

// --- Render profile card ---
function renderProfile(profile) {
  const initials = getInitials(profile);
  const name = profile.first_name
    ? `${profile.first_name} ${profile.last_name || ""}`.trim()
    : profile.username || profile.email;

  // Welcome heading
  const welcomeEl = document.getElementById("welcome-heading");
  if (welcomeEl) {
    welcomeEl.textContent = `Welcome back, ${profile.username || profile.email.split("@")[0]}!`;
  }

  // Header avatar & name
  const headerAvatar = document.getElementById("header-avatar");
  const headerUsername = document.getElementById("header-username");
  if (headerAvatar) headerAvatar.textContent = initials;
  if (headerUsername) headerUsername.textContent = name;

  // Profile card
  const card = document.getElementById("profile-card");
  if (!card) return;

  card.innerHTML = `
    <div class="avatar avatar--xl" style="margin:0 auto 14px;">${initials}</div>
    <h3 style="text-align:center; margin-bottom:2px;">${name}</h3>
    <p class="muted" style="text-align:center; margin-bottom:18px;">${profile.email}</p>
    <div class="profile-field">
      <span class="profile-field-label">Role</span>
      <span class="profile-field-value"><span class="badge badge-role">${profile.role || "USER"}</span></span>
    </div>
    <div class="profile-field">
      <span class="profile-field-label">Email</span>
      <span class="profile-field-value">
        <span class="badge ${profile.email_verified ? "badge-success" : "badge-danger"}">
          ${profile.email_verified ? "Verified" : "Unverified"}
        </span>
      </span>
    </div>
    <div class="profile-field">
      <span class="profile-field-label">Member Since</span>
      <span class="profile-field-value">${formatDate(profile.created_at)}</span>
    </div>
  `;
}

// --- Load reading stats ---
async function loadReadingStats() {
  if (!state.access) return;
  try {
    const stats = await request("/api/reading/progress/stats/", {}, true);
    const xpEl = document.getElementById("stat-xp");
    const streakEl = document.getElementById("stat-streak");
    const booksEl = document.getElementById("stat-books");
    const timeEl = document.getElementById("stat-time");

    if (xpEl) xpEl.textContent = stats.total_xp.toLocaleString();
    if (streakEl) streakEl.textContent = `${stats.current_streak} day${stats.current_streak !== 1 ? "s" : ""}`;
    if (booksEl) booksEl.textContent = stats.books_finished;
    if (timeEl) timeEl.textContent = `${stats.total_time_hours}h`;
  } catch (_) {}
}

// --- Load currently reading ---
async function loadCurrentlyReading() {
  if (!state.access) return;
  const container = document.getElementById("reading-list");
  if (!container) return;

  try {
    const data = await request("/api/reading/progress/currently-reading/", {}, true);
    const books = Array.isArray(data) ? data : data.results || [];

    if (books.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">&#128214;</div>
          <h3>No books yet</h3>
          <p>Add your first book to start tracking your reading progress.</p>
          <a href="/books/" class="ghost" style="display:inline-block;text-decoration:none;">Browse Books</a>
        </div>
      `;
      return;
    }

    container.innerHTML = books.map((ub) => {
      const book = ub.book;
      const coverHtml = book.cover_url
        ? `<img src="${escapeHtml(book.cover_url)}" alt="${escapeHtml(book.title)}" />`
        : `<div style="width:50px;height:70px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;color:var(--muted-light);">&#128214;</div>`;
      const pct = ub.progress_percent || 0;
      const pageText = book.total_pages > 0
        ? `${ub.current_page} / ${book.total_pages} pages (${pct}%)`
        : `${ub.current_page} pages read`;

      return `
        <div class="reading-item">
          <div class="reading-item-cover">${coverHtml}</div>
          <div class="reading-item-info">
            <div class="reading-item-title">${escapeHtml(book.title)}</div>
            <div class="reading-item-author">${escapeHtml(book.author)}</div>
            <div class="progress-bar">
              <div class="progress-bar-fill" style="width:${pct}%"></div>
            </div>
            <div class="reading-item-progress-text">${pageText}</div>
          </div>
        </div>
      `;
    }).join("");
  } catch (_) {
    // Keep the empty state on error
  }
}

// --- Load profile ---
async function loadProfile() {
  if (!state.access) {
    window.location.href = "/";
    return;
  }
  try {
    const profile = await request("/api/auth/profile/profile/", { method: "GET" }, true);
    renderProfile(profile);
  } catch (error) {
    clearSession();
    window.location.href = "/";
  }
}

// --- Sidebar toggle ---
function setupSidebar() {
  const toggle = document.getElementById("menu-toggle");
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebar-overlay");

  if (!toggle || !sidebar) return;

  toggle.addEventListener("click", () => {
    sidebar.classList.toggle("is-open");
    if (overlay) overlay.classList.toggle("is-visible");
  });

  if (overlay) {
    overlay.addEventListener("click", () => {
      sidebar.classList.remove("is-open");
      overlay.classList.remove("is-visible");
    });
  }
}

// --- Logout ---
function setupLogout() {
  const btns = [document.getElementById("logout-sidebar")];
  btns.forEach((btn) => {
    if (!btn) return;
    btn.addEventListener("click", async () => {
      try {
        if (state.access) {
          await request("/api/auth/logout/logout/", { method: "POST" }, true);
        }
      } catch (_) {}
      clearSession();
      window.location.href = "/";
    });
  });
}

// --- User dropdown logout ---
function setupUserDropdown() {
  const dropdown = document.getElementById("user-dropdown");
  if (!dropdown) return;
  dropdown.addEventListener("click", async () => {
    try {
      if (state.access) {
        await request("/api/auth/logout/logout/", { method: "POST" }, true);
      }
    } catch (_) {}
    clearSession();
    window.location.href = "/";
  });
}

// ============================================================
// ADD BOOK MODAL
// ============================================================

function sanitizeUrl(url) {
  if (!url) return "";
  return url.startsWith("http") ? url : "";
}

function setupAddBookModal() {
  const backdrop    = document.getElementById("add-book-backdrop");
  const openBtn     = document.getElementById("open-add-book-btn");
  const closeBtn    = document.getElementById("close-add-book-btn");
  const searchInput = document.getElementById("add-book-search");
  const resultsEl   = document.getElementById("add-book-results");
  const fileInput   = document.getElementById("ab-file-input");
  const statusEl    = document.getElementById("ab-upload-status");

  if (!backdrop || !openBtn) return;

  let allBooks = [];
  let targetBookId = null;

  // ---- Open / Close ----
  openBtn.addEventListener("click", () => {
    backdrop.style.display = "flex";
    loadCatalogBooks();
    setTimeout(() => searchInput.focus(), 120);
  });

  function resetModal() {
    backdrop.style.display = "none";
    searchInput.value = "";
    if (statusEl) statusEl.textContent = "";
    allBooks = [];
    targetBookId = null;
    resultsEl.innerHTML = '<div class="add-book-hint">&#128214; Loading catalog...</div>';
    fileInput.value = "";
  }

  closeBtn.addEventListener("click", resetModal);
  backdrop.addEventListener("click", (e) => { if (e.target === backdrop) resetModal(); });

  // ---- Client-side search filter ----
  let debounce;
  searchInput.addEventListener("input", () => {
    clearTimeout(debounce);
    debounce = setTimeout(() => renderBooks(allBooks, searchInput.value.trim()), 200);
  });

  // ---- Load catalog from API ----
  async function loadCatalogBooks() {
    resultsEl.innerHTML = '<div class="add-book-hint">&#128214; Loading catalog...</div>';
    try {
      const data = await request("/api/books/?page_size=100", {}, true);
      allBooks = Array.isArray(data) ? data : (data.results || []);
      renderBooks(allBooks, searchInput.value.trim());
    } catch (err) {
      resultsEl.innerHTML = `<div class="add-book-hint" style="color:var(--rose);">Could not load catalog — ${escapeHtml(err.message)}</div>`;
    }
  }

  // ---- Render books list ----
  function renderBooks(books, query) {
    const q = query.toLowerCase();
    const filtered = q
      ? books.filter((b) =>
          b.title.toLowerCase().includes(q) || b.author.toLowerCase().includes(q)
        )
      : books;

    if (filtered.length === 0) {
      resultsEl.innerHTML = `<div class="add-book-hint">${
        q ? "No books match your search." : "No books in the catalog yet."
      }</div>`;
      return;
    }

    resultsEl.innerHTML = filtered.map((b) => `
      <div class="add-book-result" data-book-id="${b.id}">
        <div class="add-book-result-cover">
          ${b.cover_url
            ? `<img src="${sanitizeUrl(b.cover_url)}" alt="" onerror="this.parentElement.innerHTML='&#128214;'" />`
            : "&#128214;"}
        </div>
        <div class="add-book-result-info">
          <div class="add-book-result-title">${escapeHtml(b.title)}</div>
          <div class="add-book-result-author">${escapeHtml(b.author)}</div>
          ${b.file
            ? '<span class="ab-has-pdf">&#128196; PDF attached</span>'
            : '<span class="ab-no-pdf">No PDF</span>'}
        </div>
        <button class="add-book-add-btn ${b.file ? "ab-replace" : ""}"
                data-book-id="${b.id}"
                type="button">${b.file ? "Replace" : "Attach PDF"}</button>
      </div>
    `).join("");

    resultsEl.querySelectorAll(".add-book-add-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        targetBookId = this.dataset.bookId;
        if (statusEl) statusEl.textContent = "";
        fileInput.value = "";
        fileInput.click();
      });
    });
  }

  // ---- File selected — upload to existing book ----
  fileInput.addEventListener("change", async function () {
    const file = this.files[0];
    if (!file || !targetBookId) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      if (statusEl) { statusEl.style.color = "var(--rose)"; statusEl.textContent = "Only PDF files are allowed."; }
      this.value = "";
      return;
    }

    const btn = resultsEl.querySelector(`.add-book-add-btn[data-book-id="${targetBookId}"]`);
    const originalText = btn ? btn.textContent : "";
    if (btn) { btn.disabled = true; btn.textContent = "Uploading..."; }
    if (statusEl) statusEl.textContent = "";

    const formData = new FormData();
    formData.append("file", file);

    try {
      const headers = {};
      if (state.access) headers.Authorization = `Bearer ${state.access}`;
      const resp = await fetch(`/api/books/${targetBookId}/upload-file/`, {
        method: "POST",
        headers,
        body: formData,
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(data.detail || `Upload failed (${resp.status})`);

      // Update local allBooks entry so re-render reflects the new PDF
      const idx = allBooks.findIndex((b) => String(b.id) === String(targetBookId));
      if (idx !== -1) allBooks[idx].file = data.file || true;

      if (statusEl) {
        statusEl.style.color = "#065f46";
        statusEl.textContent = `\u2713 PDF attached to "${data.title}"!`;
      }
      renderBooks(allBooks, searchInput.value.trim());
    } catch (err) {
      if (statusEl) { statusEl.style.color = "var(--rose)"; statusEl.textContent = err.message || "Upload failed. Try again."; }
      if (btn) { btn.disabled = false; btn.textContent = originalText; }
    }

    this.value = "";
    targetBookId = null;
  });
}

// --- Init ---
setupSidebar();
setupLogout();
setupUserDropdown();
setupAddBookModal();
loadProfile();
loadReadingStats();
loadCurrentlyReading();
