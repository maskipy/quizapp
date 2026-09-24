/* ===================================================================
   CPGE Flashcards -- dashboard page
   =================================================================== */

requireAuth();

const state = { limit: 20, offset: 0, total: 0 };

const decksLoading = document.getElementById("decks-loading");
const decksEmpty = document.getElementById("decks-empty");
const decksList = document.getElementById("decks-list");
const pagination = document.getElementById("pagination");
const pageInfo = document.getElementById("page-info");
const prevBtn = document.getElementById("prev-page");
const nextBtn = document.getElementById("next-page");
const dashboardError = document.getElementById("dashboard-error");
const userGreeting = document.getElementById("user-greeting");

function showError(message) {
  dashboardError.textContent = message;
  dashboardError.classList.remove("hidden");
}

function clearError() {
  dashboardError.classList.add("hidden");
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value == null ? "" : value;
  return div.innerHTML;
}

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch (e) {
    return "";
  }
}

/** Briefly highlights an element to confirm something the user just did took effect. */
function flashElement(selector, className) {
  const el = document.querySelector(selector);
  if (!el) return; // e.g. it landed on a page we're not currently viewing
  el.classList.add(className);
  el.addEventListener("animationend", () => el.classList.remove(className), { once: true });
}

async function loadUser() {
  try {
    const user = await apiFetch("/auth/me");
    userGreeting.textContent = user.full_name ? `Hi, ${user.full_name}` : user.email;
  } catch (err) {
    // A 401 here is already handled by apiFetch's redirect.
  }
}

async function loadDecks() {
  clearError();
  decksLoading.classList.remove("hidden");
  decksEmpty.classList.add("hidden");
  decksList.innerHTML = "";
  pagination.classList.add("hidden");

  try {
    const data = await apiFetch(`/decks?limit=${state.limit}&offset=${state.offset}`);
    state.total = data.total;
    decksLoading.classList.add("hidden");

    if (data.items.length === 0 && state.offset > 0) {
      // We paged past the end (e.g. after deleting the last item on a page).
      state.offset = Math.max(0, state.offset - state.limit);
      return loadDecks();
    }

    if (data.items.length === 0) {
      decksEmpty.classList.remove("hidden");
      return;
    }

    renderDecks(data.items);
    renderPagination();
  } catch (err) {
    decksLoading.classList.add("hidden");
    showError(err.message);
  }
}

function renderDecks(decks) {
  decksList.innerHTML = decks
    .map(
      (deck) => `
    <a class="deck-card" data-deck-id="${escapeHtml(deck.id)}" href="deck.html?id=${encodeURIComponent(deck.id)}">
      <h3>${escapeHtml(deck.title)}</h3>
      <p>${deck.description ? escapeHtml(deck.description) : '<span class="muted">No description</span>'}</p>
      <span class="deck-meta">Created ${formatDate(deck.created_at)}</span>
    </a>
  `
    )
    .join("");
}

function renderPagination() {
  if (state.total <= state.limit) {
    pagination.classList.add("hidden");
    return;
  }
  pagination.classList.remove("hidden");
  const start = state.offset + 1;
  const end = Math.min(state.offset + state.limit, state.total);
  pageInfo.textContent = `${start}-${end} of ${state.total}`;
  prevBtn.disabled = state.offset === 0;
  nextBtn.disabled = state.offset + state.limit >= state.total;
}

prevBtn.addEventListener("click", () => {
  state.offset = Math.max(0, state.offset - state.limit);
  loadDecks();
});

nextBtn.addEventListener("click", () => {
  if (state.offset + state.limit < state.total) {
    state.offset += state.limit;
    loadDecks();
  }
});

document.getElementById("create-deck-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  const titleInput = document.getElementById("new-deck-title");
  const descInput = document.getElementById("new-deck-desc");
  const submitBtn = document.getElementById("create-deck-submit");

  const title = titleInput.value.trim();
  const description = descInput.value.trim();
  if (!title) return;

  submitBtn.disabled = true;
  submitBtn.textContent = "Creating...";
  try {
    const newDeck = await apiFetch("/decks", {
      method: "POST",
      body: { title, description: description || null },
    });
    titleInput.value = "";
    descInput.value = "";
    state.offset = 0;
    await loadDecks();
    flashElement(`.deck-card[data-deck-id="${newDeck.id}"]`, "just-added");
  } catch (err) {
    showError(err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Create deck";
  }
});

document.getElementById("logout-btn").addEventListener("click", () => {
  clearToken();
  window.location.href = "index.html";
});

loadUser();
loadDecks();
