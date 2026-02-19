const state = {
  access: localStorage.getItem("bud_access") || "",
  refresh: localStorage.getItem("bud_refresh") || "",
};

if (state.access) {
  window.location.href = "/dashboard/";
}

const statusEl = document.getElementById("status");

function setStatus(message, isError = false) {
  statusEl.style.display = "block";
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function saveTokens(data) {
  localStorage.setItem("bud_access", data.access || "");
  localStorage.setItem("bud_refresh", data.refresh || "");
}

function wirePasswordToggles() {
  document.querySelectorAll(".toggle-password").forEach((button) => {
    button.addEventListener("click", () => {
      const input = document.getElementById(button.dataset.target);
      if (!input) return;
      const showing = input.type === "text";
      input.type = showing ? "password" : "text";
      button.classList.toggle("is-visible", !showing);
      button.setAttribute("aria-label", showing ? "Show password" : "Hide password");
    });
  });
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data.detail || data.error || JSON.stringify(data);
    throw new Error(detail || `Request failed (${response.status})`);
  }

  return data;
}

// --- Google Sign-In (rendered button in popup mode) ---
function handleGoogleCredential(response) {
  setStatus("Signing in with Google...");
  request("/api/auth/google/", {
    method: "POST",
    body: JSON.stringify({ credential: response.credential }),
  })
    .then((data) => {
      saveTokens(data);
      window.location.href = "/dashboard/";
    })
    .catch((err) => {
      setStatus(err.message, true);
    });
}

function initGoogleSignIn(clientId) {
  if (typeof google === "undefined" || !google.accounts) return;
  if (!clientId) return;

  google.accounts.id.initialize({
    client_id: clientId,
    callback: handleGoogleCredential,
  });

  // Replace our placeholder button with Google's rendered button
  const container = document.getElementById("google-signin-btn");
  container.innerHTML = "";
  google.accounts.id.renderButton(container, {
    type: "standard",
    theme: "outline",
    size: "large",
    text: "continue_with",
    shape: "rectangular",
    width: container.offsetWidth || 360,
  });
}

// Fetch client ID then init Google button
fetch("/api/auth/google-client-id/")
  .then((r) => r.json())
  .then((d) => {
    const clientId = d.client_id || "";
    if (!clientId) return;

    if (typeof google !== "undefined" && google.accounts) {
      initGoogleSignIn(clientId);
    } else {
      // GIS script still loading — wait for it
      window.addEventListener("load", () => {
        setTimeout(() => initGoogleSignIn(clientId), 300);
      });
    }
  })
  .catch(() => {});

wirePasswordToggles();

document.getElementById("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.currentTarget).entries());

  try {
    setStatus("Logging in...");
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
