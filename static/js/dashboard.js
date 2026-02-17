const state = {
  access: localStorage.getItem("bud_access") || "",
  refresh: localStorage.getItem("bud_refresh") || "",
};

const profileEl = document.getElementById("profile-json");

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

async function loadProfile() {
  if (!state.access) {
    window.location.href = "/";
    return;
  }

  try {
    const profile = await request("/api/auth/profile/profile/", { method: "GET" }, true);
    profileEl.textContent = JSON.stringify(profile, null, 2);
  } catch (error) {
    clearSession();
    window.location.href = "/";
  }
}

document.getElementById("logout").addEventListener("click", async () => {
  try {
    if (state.access) {
      await request("/api/auth/logout/logout/", { method: "POST" }, true);
    }
  } catch (_) {
    // Keep local logout behavior even if endpoint fails.
  }

  clearSession();
  window.location.href = "/";
});

loadProfile();
