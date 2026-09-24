/* ===================================================================
   CPGE Flashcards -- login / register page
   =================================================================== */

const tabLogin = document.getElementById("tab-login");
const tabRegister = document.getElementById("tab-register");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const errorBox = document.getElementById("error-box");

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

function clearError() {
  errorBox.classList.add("hidden");
  errorBox.textContent = "";
}

const TAB_SWITCH_MS = 150;

function switchTab(which) {
  const showLogin = which === "login";
  const from = showLogin ? registerForm : loginForm;
  const to = showLogin ? loginForm : registerForm;

  if (from.classList.contains("hidden")) return; // already on that tab

  clearError();
  tabLogin.classList.toggle("active", showLogin);
  tabRegister.classList.toggle("active", !showLogin);

  from.classList.add("anim-fade-out");
  setTimeout(() => {
    from.classList.add("hidden");
    from.classList.remove("anim-fade-out");
    to.classList.remove("hidden");
    to.classList.add("anim-fade-in");
    setTimeout(() => to.classList.remove("anim-fade-in"), 250);
  }, TAB_SWITCH_MS);
}

tabLogin.addEventListener("click", () => switchTab("login"));
tabRegister.addEventListener("click", () => switchTab("register"));

function setButtonBusy(button, busyText) {
  button.disabled = true;
  button.dataset.originalText = button.textContent;
  button.textContent = busyText;
}

function resetButton(button) {
  button.disabled = false;
  if (button.dataset.originalText) button.textContent = button.dataset.originalText;
}

async function loginWithCredentials(email, password) {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  const data = await apiFetch("/auth/login", {
    method: "POST",
    body,
    isForm: true,
    auth: false,
  });
  setToken(data.access_token);
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  const submitBtn = document.getElementById("login-submit");
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;

  setButtonBusy(submitBtn, "Logging in...");
  try {
    await loginWithCredentials(email, password);
    window.location.href = "dashboard.html";
  } catch (err) {
    showError(err.message);
    resetButton(submitBtn);
  }
});

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  const submitBtn = document.getElementById("register-submit");
  const fullName = document.getElementById("register-name").value.trim();
  const email = document.getElementById("register-email").value.trim();
  const password = document.getElementById("register-password").value;

  setButtonBusy(submitBtn, "Creating account...");
  try {
    await apiFetch("/auth/register", {
      method: "POST",
      body: { email, full_name: fullName || null, password },
      auth: false,
    });
    // Registration doesn't return a token, so log in right after.
    await loginWithCredentials(email, password);
    window.location.href = "dashboard.html";
  } catch (err) {
    showError(err.message);
    resetButton(submitBtn);
  }
});

// If a token is already stored and still valid, skip straight to the dashboard.
(async function checkExistingSession() {
  if (!isLoggedIn()) return;
  try {
    await apiFetch("/auth/me");
    window.location.href = "dashboard.html";
  } catch (err) {
    clearToken();
  }
})();
