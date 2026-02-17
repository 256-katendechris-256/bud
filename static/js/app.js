const state = {
  access: localStorage.getItem("bud_access") || "",
  refresh: localStorage.getItem("bud_refresh") || "",
};

if (state.access) {
  window.location.href = "/dashboard/";
}

const statusEl = document.getElementById("status");
const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function setTab(tabId) {
  tabs.forEach((tab) => tab.classList.toggle("is-active", tab.dataset.tab === tabId));
  panels.forEach((panel) => panel.classList.toggle("is-active", panel.id === tabId));
}

function saveTokens(data) {
  state.access = data.access || "";
  state.refresh = data.refresh || "";
  if (state.access) {
    localStorage.setItem("bud_access", state.access);
  }
  if (state.refresh) {
    localStorage.setItem("bud_refresh", state.refresh);
  }
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

tabs.forEach((tab) => {
  tab.addEventListener("click", () => setTab(tab.dataset.tab));
});

document.querySelectorAll(".toggle-password").forEach((button) => {
  button.addEventListener("click", () => {
    const input = document.getElementById(button.dataset.target);
    if (!input) {
      return;
    }
    const showing = input.type === "text";
    input.type = showing ? "password" : "text";
    button.classList.toggle("is-visible", !showing);
    button.setAttribute("aria-label", showing ? "Show password" : "Hide password");
  });
});

document.getElementById("login").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = Object.fromEntries(formData.entries());

  try {
    const data = await request("/api/auth/login/", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    saveTokens(data);
    window.location.href = "/dashboard/";
  } catch (error) {
    setStatus(error.message, true);
  }
});

document.getElementById("register").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = Object.fromEntries(formData.entries());

  try {
    await request("/api/auth/register/", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    setStatus("Registration complete. Enter the 6-digit verification code from your email.");
    setTab("verify");
  } catch (error) {
    setStatus(error.message, true);
  }
});

document.getElementById("verify").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const payload = Object.fromEntries(formData.entries());

  try {
    const data = await request("/api/auth/register/verify_email/", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    saveTokens(data);
    window.location.href = data.redirect || "/dashboard/";
  } catch (error) {
    setStatus(error.message, true);
  }
});

(() => {
  const token = new URLSearchParams(window.location.search).get("token");
  if (token) {
    const verifyInput = document.querySelector("#verify input[name='token']");
    verifyInput.value = token;
    setTab("verify");
    setStatus("Verification code found in URL. Submit to continue.");
  }
})();
