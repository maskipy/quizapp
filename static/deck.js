/* ===================================================================
   CPGE Flashcards -- deck view page
   =================================================================== */

requireAuth();

const params = new URLSearchParams(window.location.search);
const deckId = params.get("id");
if (!deckId) {
  window.location.href = "dashboard.html";
}

let currentDeck = null;

const loadingEl = document.getElementById("deck-loading");
const loadErrorEl = document.getElementById("load-error");
const pageContent = document.getElementById("page-content");

const titleDisplay = document.getElementById("deck-title-display");
const descDisplay = document.getElementById("deck-desc-display");
const editCollapsible = document.getElementById("edit-deck-collapsible");
const editForm = document.getElementById("edit-deck-form");
const editTitleInput = document.getElementById("edit-deck-title");
const editDescInput = document.getElementById("edit-deck-desc");
const deckActionError = document.getElementById("deck-action-error");

const cardCountEl = document.getElementById("card-count");
const cardsEmptyEl = document.getElementById("cards-empty");
const cardsListEl = document.getElementById("cards-list");
const cardErrorEl = document.getElementById("card-error");
const studyBtn = document.getElementById("study-btn");

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value == null ? "" : value;
  return div.innerHTML;
}

/** Briefly highlights an element to confirm something the user just did took effect. */
function flashElement(selector, className) {
  const el = document.querySelector(selector);
  if (!el) return;
  el.classList.add(className);
  el.addEventListener("animationend", () => el.classList.remove(className), { once: true });
}

function showLoadError(message) {
  loadingEl.classList.add("hidden");
  pageContent.classList.add("hidden");
  loadErrorEl.textContent = message;
  loadErrorEl.classList.remove("hidden");
}

function showDeckActionError(message) {
  deckActionError.textContent = message;
  deckActionError.classList.remove("hidden");
}

function clearDeckActionError() {
  deckActionError.classList.add("hidden");
}

function showCardError(message) {
  cardErrorEl.textContent = message;
  cardErrorEl.classList.remove("hidden");
}

function clearCardError() {
  cardErrorEl.classList.add("hidden");
}

async function loadDeck() {
  loadErrorEl.classList.add("hidden");
  try {
    const deck = await apiFetch(`/decks/${encodeURIComponent(deckId)}`);
    currentDeck = deck;
    loadingEl.classList.add("hidden");
    pageContent.classList.remove("hidden");
    renderDeck();
  } catch (err) {
    if (err.status === 404) {
      showLoadError("This deck isn't available. It may have been deleted, or it belongs to another account.");
    } else {
      showLoadError(err.message);
    }
  }
}

function renderDeck() {
  document.title = `${currentDeck.title} -- CPGE Flashcards`;
  titleDisplay.textContent = currentDeck.title;
  descDisplay.textContent = currentDeck.description || "No description";
  editTitleInput.value = currentDeck.title;
  editDescInput.value = currentDeck.description || "";
  renderCards();
}

function renderCards() {
  const cards = currentDeck.cards || [];
  cardCountEl.textContent = cards.length;
  studyBtn.disabled = cards.length === 0;

  if (cards.length === 0) {
    cardsEmptyEl.classList.remove("hidden");
    cardsListEl.innerHTML = "";
    return;
  }
  cardsEmptyEl.classList.add("hidden");

  cardsListEl.innerHTML = cards
    .map(
      (card) => `
    <div class="card-item" data-card-id="${escapeHtml(card.id)}">
      <div class="card-view">
        <div class="card-field"><span class="card-label">Q</span><span class="card-q">${escapeHtml(card.question)}</span></div>
        <div class="card-field"><span class="card-label">A</span><span class="card-a">${escapeHtml(card.answer)}</span></div>
        <div class="card-item-actions">
          <button type="button" class="btn btn-secondary btn-sm edit-card-btn">Edit</button>
          <button type="button" class="btn btn-danger btn-sm delete-card-btn">Delete</button>
        </div>
      </div>
      <div class="collapsible card-edit-collapsible">
        <div class="collapsible-inner">
          <form class="card-edit-form stacked-form">
            <label>Question</label>
            <textarea class="edit-card-question" rows="2" maxlength="2000">${escapeHtml(card.question)}</textarea>
            <label>Answer</label>
            <textarea class="edit-card-answer" rows="2" maxlength="2000">${escapeHtml(card.answer)}</textarea>
            <div class="form-row-buttons">
              <button type="submit" class="btn btn-primary btn-sm">Save changes</button>
              <button type="button" class="btn btn-ghost btn-sm cancel-edit-card">Cancel</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `
    )
    .join("");

  cardsListEl.querySelectorAll(".card-item").forEach((itemEl) => {
    const cardId = itemEl.dataset.cardId;
    const viewEl = itemEl.querySelector(".card-view");
    const editCollapsibleEl = itemEl.querySelector(".card-edit-collapsible");
    const editEl = itemEl.querySelector(".card-edit-form");

    itemEl.querySelector(".edit-card-btn").addEventListener("click", () => {
      viewEl.classList.add("hidden");
      editCollapsibleEl.classList.add("open");
    });

    itemEl.querySelector(".cancel-edit-card").addEventListener("click", () => {
      editCollapsibleEl.classList.remove("open");
      viewEl.classList.remove("hidden");
    });

    itemEl.querySelector(".delete-card-btn").addEventListener("click", async () => {
      if (!confirm("Delete this card? This cannot be undone.")) return;
      clearCardError();
      try {
        await apiFetch(`/decks/${encodeURIComponent(deckId)}/cards/${encodeURIComponent(cardId)}`, {
          method: "DELETE",
        });
        await loadDeck();
      } catch (err) {
        showCardError(err.message);
      }
    });

    editEl.addEventListener("submit", async (event) => {
      event.preventDefault();
      const question = editEl.querySelector(".edit-card-question").value.trim();
      const answer = editEl.querySelector(".edit-card-answer").value.trim();
      if (!question || !answer) return;
      clearCardError();
      try {
        await apiFetch(`/decks/${encodeURIComponent(deckId)}/cards/${encodeURIComponent(cardId)}`, {
          method: "PATCH",
          body: { question, answer },
        });
        await loadDeck();
        flashElement(`.card-item[data-card-id="${cardId}"]`, "just-updated");
      } catch (err) {
        showCardError(err.message);
      }
    });
  });
}

document.getElementById("create-card-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  clearCardError();

  const questionInput = document.getElementById("new-card-question");
  const answerInput = document.getElementById("new-card-answer");
  const submitBtn = document.getElementById("create-card-submit");

  const question = questionInput.value.trim();
  const answer = answerInput.value.trim();
  if (!question || !answer) return;

  submitBtn.disabled = true;
  submitBtn.textContent = "Adding...";
  try {
    const newCard = await apiFetch(`/decks/${encodeURIComponent(deckId)}/cards`, {
      method: "POST",
      body: { question, answer },
    });
    questionInput.value = "";
    answerInput.value = "";
    await loadDeck();
    flashElement(`.card-item[data-card-id="${newCard.id}"]`, "just-added");
  } catch (err) {
    showCardError(err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Add card";
  }
});

document.getElementById("edit-deck-btn").addEventListener("click", () => {
  clearDeckActionError();
  editCollapsible.classList.add("open");
});

document.getElementById("cancel-edit-deck").addEventListener("click", () => {
  editCollapsible.classList.remove("open");
});

editForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearDeckActionError();

  const title = editTitleInput.value.trim();
  const description = editDescInput.value.trim();
  if (!title) return;

  try {
    await apiFetch(`/decks/${encodeURIComponent(deckId)}`, {
      method: "PATCH",
      body: { title, description: description || null },
    });
    editCollapsible.classList.remove("open");
    await loadDeck();
    flashElement("#deck-info-panel .deck-header", "just-updated");
  } catch (err) {
    showDeckActionError(err.message);
  }
});

document.getElementById("delete-deck-btn").addEventListener("click", async () => {
  if (!confirm("Delete this deck and all its cards? This cannot be undone.")) return;
  clearDeckActionError();
  try {
    await apiFetch(`/decks/${encodeURIComponent(deckId)}`, { method: "DELETE" });
    window.location.href = "dashboard.html";
  } catch (err) {
    showDeckActionError(err.message);
  }
});

studyBtn.addEventListener("click", () => {
  window.location.href = `study.html?id=${encodeURIComponent(deckId)}`;
});

document.getElementById("logout-btn").addEventListener("click", () => {
  clearToken();
  window.location.href = "index.html";
});

loadDeck();
