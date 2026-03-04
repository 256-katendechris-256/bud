/* ============================================================
   BUD — Books Browse, Search & CRUD
   ============================================================ */

const state = {
  access: localStorage.getItem("bud_access") || "",
  refresh: localStorage.getItem("bud_refresh") || "",
  activeTab: "catalog",
  query: "",
  loading: false,
  isAdmin: false,
  userRole: "",
  userId: null,
  // Cache current results so we can open modals from them
  catalogBooks: [],
  googleBooks: [],
  genres: [],
  selectedGenres: [],
  // Keyed by book id → { current_page, status }
  userProgress: {},
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
  if (options.method === "DELETE" && response.status === 204) return {};
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail || data.error || JSON.stringify(data);
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return data;
}

async function uploadFile(path, file) {
  const formData = new FormData();
  formData.append("file", file);
  const headers = {};
  if (state.access) {
    headers.Authorization = `Bearer ${state.access}`;
  }
  const response = await fetch(path, { method: "POST", headers, body: formData });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail || data.file?.[0] || JSON.stringify(data);
    throw new Error(detail || `Upload failed (${response.status})`);
  }
  return data;
}

// --- DOM refs ---
const searchInput = document.getElementById("books-search");
const grid = document.getElementById("books-grid");
const emptyState = document.getElementById("empty-state");
const emptyTitle = document.getElementById("empty-title");
const emptyMessage = document.getElementById("empty-message");
const resultsCount = document.getElementById("results-count");
const tabs = document.querySelectorAll(".books-tab");
const modalOverlay = document.getElementById("book-modal");
const modalBody = document.getElementById("modal-body");
const modalTitle = document.getElementById("modal-title");
const modalClose = document.getElementById("modal-close");

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

/**
 * Sanitize HTML from Google Books descriptions.
 * Allows safe tags (b, i, em, strong, br, p) and strips everything else.
 */
function sanitizeHtml(html) {
  if (!html) return "";
  const allowed = ["B", "I", "EM", "STRONG", "BR", "P", "UL", "OL", "LI"];
  const doc = new DOMParser().parseFromString(html, "text/html");
  function clean(node) {
    const children = Array.from(node.childNodes);
    children.forEach((child) => {
      if (child.nodeType === Node.TEXT_NODE) return;
      if (child.nodeType === Node.ELEMENT_NODE) {
        // Remove all attributes (onclick, onerror, style, etc.)
        Array.from(child.attributes).forEach((attr) => child.removeAttribute(attr.name));
        if (allowed.includes(child.tagName)) {
          clean(child);
        } else {
          // Replace disallowed tag with its text content
          child.replaceWith(...child.childNodes);
        }
      } else {
        child.remove();
      }
    });
  }
  clean(doc.body);
  return doc.body.innerHTML;
}

// --- Toast ---
function showToast(title, message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const icons = { success: "&#9989;", error: "&#10060;", info: "&#8505;&#65039;" };
  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <div class="toast-body">
      <div class="toast-title">${escapeHtml(title)}</div>
      <div class="toast-message">${escapeHtml(message)}</div>
    </div>
    <button class="toast-close" onclick="this.parentElement.remove()" type="button">&#10005;</button>
  `;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// --- Skeletons ---
function showSkeletons(count = 8) {
  grid.innerHTML = Array(count)
    .fill(0)
    .map(
      () => `
    <div class="book-card-skeleton">
      <div class="skeleton-cover"></div>
      <div class="skeleton-body">
        <div class="skeleton skeleton--title" style="width:80%;"></div>
        <div class="skeleton skeleton--text" style="width:60%;"></div>
      </div>
    </div>`
    )
    .join("");
  emptyState.style.display = "none";
  resultsCount.textContent = "";
}

// --- Render book card ---
function renderBookCard(book, isGoogle = false) {
  const title = escapeHtml(book.title || "Untitled");
  const author = escapeHtml(book.author || "Unknown Author");
  const pages = book.total_pages || 0;
  const id = isGoogle ? book.google_books_id : book.id;

  const coverHtml = book.cover_url
    ? `<img src="${escapeHtml(book.cover_url)}" alt="${title}" loading="lazy" onerror="this.parentElement.innerHTML='&#128214;'" />`
    : "&#128214;";

  const sourceLabel = isGoogle
    ? `<span class="badge badge-info" style="font-size:0.7rem;">Google</span>`
    : `<span class="badge badge-success" style="font-size:0.7rem;">In Catalog</span>`;

  return `
    <div class="book-card" data-id="${escapeHtml(String(id))}" data-source="${isGoogle ? "google" : "catalog"}" onclick="openBookModal('${escapeHtml(String(id))}', '${isGoogle ? "google" : "catalog"}')">
      <div class="book-card-cover">${coverHtml}</div>
      <div class="book-card-body">
        <div class="book-card-title" title="${title}">${title}</div>
        <div class="book-card-author">${author}</div>
        <div class="book-card-meta">
          <span class="book-card-pages">${pages > 0 ? pages + " pg" : ""}</span>
          ${sourceLabel}
        </div>
      </div>
    </div>`;
}

// --- Render results ---
function renderResults(books, isGoogle = false) {
  state.loading = false;

  // Cache results
  if (isGoogle) {
    state.googleBooks = books || [];
  } else {
    state.catalogBooks = books || [];
  }

  if (!books || books.length === 0) {
    grid.innerHTML = "";
    emptyState.style.display = "flex";
    resultsCount.textContent = "";

    if (state.query) {
      emptyTitle.textContent = "No results found";
      emptyMessage.textContent = isGoogle
        ? `No Google Books results for "${state.query}". Try a different search.`
        : `No books in the catalog match "${state.query}". Try searching Google Books.`;
    } else {
      emptyTitle.textContent = "No books yet";
      emptyMessage.textContent = "Start by searching for a book or switch to Google Books to add new ones.";
    }
    return;
  }

  emptyState.style.display = "none";
  resultsCount.textContent = `${books.length} book${books.length !== 1 ? "s" : ""} found`;
  grid.innerHTML = books.map((b) => renderBookCard(b, isGoogle)).join("");
}

// --- Genre Filters ---
const genreFiltersEl = document.getElementById("genre-filters");

async function fetchGenres() {
  try {
    const data = await request("/api/genres/", {}, true);
    const genres = Array.isArray(data) ? data : data.results || [];
    state.genres = genres;
    renderGenreChips();
  } catch (_) {}
}

async function fetchUserProgress() {
  if (!state.access) return;
  try {
    const data = await request("/api/reading/progress/", {}, true);
    const items = Array.isArray(data) ? data : data.results || [];
    state.userProgress = {};
    items.forEach((ub) => {
      if (ub.book && ub.book.id != null) {
        state.userProgress[ub.book.id] = {
          current_page: ub.current_page,
          status: ub.status,
        };
      }
    });
  } catch (_) {}
}

function renderGenreChips() {
  if (!genreFiltersEl || state.genres.length === 0) return;
  genreFiltersEl.innerHTML = state.genres
    .map(
      (g) =>
        `<button class="genre-chip ${state.selectedGenres.includes(g.id) ? "is-active" : ""}" data-genre-id="${g.id}" type="button">${escapeHtml(g.name)}</button>`
    )
    .join("");

  genreFiltersEl.querySelectorAll(".genre-chip").forEach((btn) => {
    btn.addEventListener("click", () => toggleGenre(parseInt(btn.dataset.genreId)));
  });
}

function toggleGenre(id) {
  const idx = state.selectedGenres.indexOf(id);
  if (idx === -1) {
    state.selectedGenres.push(id);
  } else {
    state.selectedGenres.splice(idx, 1);
  }
  renderGenreChips();
  fetchCatalog(state.query);
}

// --- Fetch catalog ---
async function fetchCatalog(query = "") {
  if (!state.access) { window.location.href = "/"; return; }
  state.loading = true;
  showSkeletons();
  try {
    let endpoint = query ? `/api/books/?q=${encodeURIComponent(query)}` : "/api/books/";
    if (state.selectedGenres.length > 0) {
      const sep = endpoint.includes("?") ? "&" : "?";
      endpoint += sep + state.selectedGenres.map((id) => `genre=${id}`).join("&");
    }
    const data = await request(endpoint, {}, true);
    const books = Array.isArray(data) ? data : data.results || [];
    renderResults(books, false);
  } catch (err) {
    renderResults([], false);
  }
}

// --- Fetch Google ---
async function fetchGoogle(query) {
  if (!query) {
    renderResults([], true);
    return;
  }
  if (!state.access) { window.location.href = "/"; return; }
  state.loading = true;
  showSkeletons();
  try {
    const data = await request(`/api/books/search-google/?q=${encodeURIComponent(query)}`, {}, true);
    const books = Array.isArray(data) ? data : data.results || [];
    renderResults(books, true);
  } catch (err) {
    renderResults([], true);
  }
}

// ============================================================
// MODAL — Book Detail
// ============================================================

function openModal() {
  modalOverlay.classList.add("is-open");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  modalOverlay.classList.remove("is-open");
  document.body.style.overflow = "";
}

modalClose.addEventListener("click", closeModal);
modalOverlay.addEventListener("click", (e) => {
  if (e.target === modalOverlay) closeModal();
});

function openBookModal(id, source) {
  let book;
  if (source === "google") {
    book = state.googleBooks.find((b) => b.google_books_id === id);
    if (book) showGoogleBookModal(book);
  } else {
    book = state.catalogBooks.find((b) => String(b.id) === String(id));
    if (book) showCatalogBookModal(book);
  }
}
window.openBookModal = openBookModal;

// --- Google Book Modal (with Add to Bud) ---
function showGoogleBookModal(book) {
  modalTitle.textContent = "Google Books";

  const coverHtml = book.cover_url
    ? `<img src="${escapeHtml(book.cover_url)}" alt="${escapeHtml(book.title)}" onerror="this.parentElement.innerHTML='&#128214;'" />`
    : "&#128214;";

  const desc = book.description
    ? `<div class="modal-book-description">${sanitizeHtml(book.description)}</div>`
    : "";

  const categories = (book.categories || [])
    .map((c) => `<span class="badge badge-info">${escapeHtml(c)}</span>`)
    .join("");

  modalBody.innerHTML = `
    <div class="modal-book-top">
      <div class="modal-book-cover">${coverHtml}</div>
      <div class="modal-book-info">
        <h3>${escapeHtml(book.title)}</h3>
        <div class="modal-book-author">${escapeHtml(book.author)}</div>
        <div class="modal-book-badges">
          ${book.total_pages ? `<span class="badge badge-success">${book.total_pages} pages</span>` : ""}
          ${book.language ? `<span class="badge badge-role">${escapeHtml(book.language.toUpperCase())}</span>` : ""}
          ${book.publisher ? `<span class="badge badge-info">${escapeHtml(book.publisher)}</span>` : ""}
          ${book.published_date ? `<span class="badge badge-info">${escapeHtml(book.published_date)}</span>` : ""}
        </div>
        ${categories ? `<div class="modal-book-badges">${categories}</div>` : ""}
      </div>
    </div>
    ${desc}
    <div class="modal-actions">
      <button id="modal-add-btn" type="button" data-gid="${escapeHtml(book.google_books_id)}">
        Add to Bud Catalog
      </button>
    </div>
  `;

  document.getElementById("modal-add-btn").addEventListener("click", async function () {
    const btn = this;
    const gid = btn.dataset.gid;
    btn.disabled = true;
    btn.textContent = "Adding...";

    try {
      await request(
        "/api/books/add-from-google/",
        { method: "POST", body: JSON.stringify({ google_books_id: gid }) },
        true
      );
      btn.textContent = "Added to Bud!";
      btn.classList.add("added");
      btn.style.background = "var(--success-bg)";
      btn.style.color = "var(--success-ink)";
      btn.style.boxShadow = "none";
      showToast("Book added", `"${book.title}" is now in the Bud catalog.`, "success");
    } catch (err) {
      btn.textContent = "Failed — Try Again";
      btn.disabled = false;
      showToast("Error", err.message || "Could not add book.", "error");
    }
  });

  openModal();
}

// --- Catalog Book Modal ---
function showCatalogBookModal(book) {
  modalTitle.textContent = "Book Details";

  const coverHtml = book.cover_url
    ? `<img src="${escapeHtml(book.cover_url)}" alt="${escapeHtml(book.title)}" onerror="this.parentElement.innerHTML='&#128214;'" />`
    : "&#128214;";

  const genres = (book.genres || [])
    .map((g) => `<span class="badge badge-info">${escapeHtml(g.name)}</span>`)
    .join("");

  // Current reading progress for this book
  const progress = state.userProgress[book.id];
  const currentPage = progress ? progress.current_page : 0;
  const pageLabel = currentPage > 0 ? ` · p.${currentPage}` : "";

  // Read button — shows page number if user has started
  const readBtn = book.file
    ? `<a href="/books/${book.id}/read/"
          id="modal-read-btn"
          style="flex:1;min-width:140px;display:inline-flex;align-items:center;justify-content:center;gap:6px;text-decoration:none;">
         &#128214; Read${escapeHtml(pageLabel)}
       </a>`
    : `<button class="ghost" disabled style="flex:1;min-width:140px;opacity:0.5;">No PDF yet</button>`;

  // Remove button — only for the uploader or admin
  const canRemove = book.added_by === state.userId || state.isAdmin;
  const removeBtn = canRemove
    ? `<button id="modal-remove-btn" class="ghost" type="button"
          style="min-width:44px;flex-shrink:0;color:var(--rose);border-color:var(--rose);"
          title="Remove book">&#128465;</button>`
    : "";

  // Admin edit button
  const editBtn = state.isAdmin
    ? `<button class="ghost" id="modal-edit-btn" type="button" style="flex:1;min-width:100px;">Edit</button>`
    : "";

  modalBody.innerHTML = `
    <!-- Detail View -->
    <div id="modal-detail-view">
      <div class="modal-book-top">
        <div class="modal-book-cover">${coverHtml}</div>
        <div class="modal-book-info">
          <h3>${escapeHtml(book.title)}</h3>
          <div class="modal-book-author">${escapeHtml(book.author)}</div>
          <div class="modal-book-badges">
            ${book.total_pages ? `<span class="badge badge-success">${book.total_pages} pages</span>` : ""}
            ${genres}
          </div>
          ${progress ? `<div style="margin-top:8px;font-size:0.8rem;color:var(--muted);">
            ${progress.status === "FINISHED" ? "&#10003; Finished" : `Reading — p.${currentPage}`}
          </div>` : ""}
        </div>
      </div>
      ${book.description ? `<div class="modal-book-description">${sanitizeHtml(book.description)}</div>` : ""}
      <div class="modal-actions">
        ${readBtn}
        ${editBtn}
        ${removeBtn}
      </div>
    </div>

    <!-- Edit Form (hidden by default, admin only) -->
    <div class="edit-form" id="modal-edit-form">
      <div class="form-grid">
        <label class="full">Title
          <input type="text" id="edit-title" value="${escapeHtml(book.title)}" />
        </label>
        <label class="full">Author
          <input type="text" id="edit-author" value="${escapeHtml(book.author)}" />
        </label>
        <label>Pages
          <input type="number" id="edit-pages" value="${book.total_pages || 0}" min="0" />
        </label>
        <label>Language
          <input type="text" id="edit-language" value="${escapeHtml(book.language || "en")}" />
        </label>
        <label class="full">Cover URL
          <input type="url" id="edit-cover" value="${escapeHtml(book.cover_url || "")}" />
        </label>
        <label class="full">Publisher
          <input type="text" id="edit-publisher" value="${escapeHtml(book.publisher || "")}" />
        </label>
        <label class="full">Description
          <textarea id="edit-description">${escapeHtml(book.description || "")}</textarea>
        </label>
      </div>
      <div class="modal-actions">
        <button id="edit-save-btn" type="button">Save Changes</button>
        <button class="ghost" id="edit-cancel-btn" type="button">Cancel</button>
      </div>
    </div>
  `;

  // Wire up Remove button
  if (canRemove) {
    document.getElementById("modal-remove-btn").addEventListener("click", async function () {
      if (!confirm(`Remove "${book.title}" from the catalog? This cannot be undone.`)) return;
      this.disabled = true;
      this.textContent = "...";
      try {
        await request(`/api/books/${book.id}/`, { method: "DELETE" }, true);
        showToast("Removed", `"${book.title}" has been removed.`, "success");
        closeModal();
        fetchCatalog(state.query);
      } catch (err) {
        this.disabled = false;
        this.innerHTML = "&#128465;";
        showToast("Error", err.message || "Could not remove book.", "error");
      }
    });
  }

  // Wire up admin Edit
  if (state.isAdmin) {
    const editForm = document.getElementById("modal-edit-form");
    const detailView = document.getElementById("modal-detail-view");

    document.getElementById("modal-edit-btn").addEventListener("click", () => {
      detailView.style.display = "none";
      editForm.classList.add("is-active");
      modalTitle.textContent = "Edit Book";
    });

    document.getElementById("edit-cancel-btn").addEventListener("click", () => {
      editForm.classList.remove("is-active");
      detailView.style.display = "block";
      modalTitle.textContent = "Book Details";
    });

    document.getElementById("edit-save-btn").addEventListener("click", async function () {
      this.disabled = true;
      this.textContent = "Saving...";
      const payload = {
        title: document.getElementById("edit-title").value.trim(),
        author: document.getElementById("edit-author").value.trim(),
        total_pages: parseInt(document.getElementById("edit-pages").value) || 0,
        language: document.getElementById("edit-language").value.trim(),
        cover_url: document.getElementById("edit-cover").value.trim(),
        publisher: document.getElementById("edit-publisher").value.trim(),
        description: document.getElementById("edit-description").value.trim(),
      };
      try {
        await request(`/api/books/${book.id}/`, { method: "PATCH", body: JSON.stringify(payload) }, true);
        showToast("Book updated", `"${payload.title}" has been updated.`, "success");
        closeModal();
        fetchCatalog(state.query);
      } catch (err) {
        this.disabled = false;
        this.textContent = "Save Changes";
        showToast("Error", err.message || "Could not update book.", "error");
      }
    });
  }

  openModal();
}

// ============================================================
// SEARCH & TABS
// ============================================================

let debounceTimer = null;
function handleSearch() {
  const query = searchInput.value.trim();
  state.query = query;

  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    if (state.activeTab === "catalog") {
      fetchCatalog(query);
    } else {
      fetchGoogle(query);
    }
  }, 300);
}

function switchTab(tab) {
  state.activeTab = tab;
  tabs.forEach((t) => {
    t.classList.toggle("is-active", t.dataset.tab === tab);
  });

  const query = searchInput.value.trim();
  state.query = query;

  if (tab === "catalog") {
    searchInput.placeholder = "Search books by title or author...";
    if (genreFiltersEl) genreFiltersEl.style.display = "";
    fetchCatalog(query);
  } else {
    searchInput.placeholder = "Search Google Books...";
    if (genreFiltersEl) genreFiltersEl.style.display = "none";
    if (query) {
      fetchGoogle(query);
    } else {
      grid.innerHTML = "";
      emptyState.style.display = "flex";
      emptyTitle.textContent = "Search Google Books";
      emptyMessage.textContent = "Type a book title or author to search millions of books.";
      resultsCount.textContent = "";
    }
  }
}

// ============================================================
// PROFILE & AUTH
// ============================================================

async function loadProfile() {
  if (!state.access) { window.location.href = "/"; return; }
  try {
    const profile = await request("/api/auth/profile/profile/", { method: "GET" }, true);
    const initials = getInitials(profile);
    const name = profile.first_name
      ? `${profile.first_name} ${profile.last_name || ""}`.trim()
      : profile.username || profile.email;

    const headerAvatar = document.getElementById("header-avatar");
    const headerUsername = document.getElementById("header-username");
    if (headerAvatar) headerAvatar.textContent = initials;
    if (headerUsername) headerUsername.textContent = name;

    // Check admin role
    state.userRole = profile.role || "";
    state.isAdmin = ["SUPER_ADMIN", "CLUB_ADMIN"].includes(profile.role) || profile.is_staff;
    state.userId = profile.id;
  } catch {
    clearSession();
    window.location.href = "/";
  }
}

// ============================================================
// SIDEBAR & LOGOUT (same as dashboard)
// ============================================================

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

function setupLogout() {
  const btn = document.getElementById("logout-sidebar");
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
}

// ============================================================
// INIT
// ============================================================

searchInput.addEventListener("input", handleSearch);
tabs.forEach((t) => t.addEventListener("click", () => switchTab(t.dataset.tab)));

// Close modal on Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});

setupSidebar();
setupLogout();
loadProfile();
fetchGenres();
fetchUserProgress();
fetchCatalog();
