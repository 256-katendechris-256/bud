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

// --- Init ---
setupSidebar();
setupLogout();
setupUserDropdown();
loadProfile();
