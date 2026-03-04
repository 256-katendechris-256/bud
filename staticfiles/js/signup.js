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

  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Server error (${response.status}). Please try again.`);
  }

  if (!response.ok) {
    const detail =
      data.detail ||
      data.error ||
      Object.values(data)
        .flat()
        .join(". ") ||
      `Request failed (${response.status})`;
    throw new Error(detail);
  }

  return data;
}

// --- Step indicator ---
function activateStep(stepNum) {
  document.getElementById("step-1").classList.toggle("active", stepNum === 1);
  document.getElementById("step-2").classList.toggle("active", stepNum === 2);
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

fetch("/api/auth/google-client-id/")
  .then((r) => r.json())
  .then((d) => {
    const clientId = d.client_id || "";
    if (!clientId) return;

    if (typeof google !== "undefined" && google.accounts) {
      initGoogleSignIn(clientId);
    } else {
      window.addEventListener("load", () => {
        setTimeout(() => initGoogleSignIn(clientId), 300);
      });
    }
  })
  .catch(() => {});

wirePasswordToggles();

document.getElementById("register-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.currentTarget).entries());

  try {
    setStatus("Creating your account...");
    await request("/api/auth/register/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setStatus("Account created! Enter the 6-digit code from your email.");
    document.getElementById("verify-form").classList.add("is-active");
    activateStep(2);
  } catch (error) {
    setStatus(error.message, true);
  }
});

document.getElementById("verify-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.currentTarget).entries());

  try {
    setStatus("Verifying...");
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
    const verifyInput = document.querySelector("#verify-form input[name='token']");
    verifyInput.value = token;
    document.getElementById("verify-form").classList.add("is-active");
    activateStep(2);
    setStatus("Verification code found in URL. Submit to continue.");
  }
})();
