/* ===================================================================
   CPGE Flashcards -- study mode page
   =================================================================== */

requireAuth();

const params = new URLSearchParams(window.location.search);
const deckId = params.get("id");
if (!deckId) {
  window.location.href = "dashboard.html";
}

// Point every "back to deck" link at this specific deck.
const deckLink = `deck.html?id=${encodeURIComponent(deckId)}`;
document.getElementById("back-to-deck").href = deckLink;
document.getElementById("empty-back-btn").href = deckLink;
document.getElementById("complete-back-btn").href = deckLink;

// Skip the flip-back delay entirely for anyone who has asked for reduced motion.
const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const FLIP_BACK_MS = REDUCED_MOTION ? 0 : 380;

let cards = [];
let currentIndex = 0;
let answerShown = false;

const loadingEl = document.getElementById("study-loading");
const errorEl = document.getElementById("study-error");
const emptyEl = document.getElementById("study-empty");
const contentEl = document.getElementById("study-content");
const completeEl = document.getElementById("study-complete");

const cardInner = document.getElementById("study-card-inner");
const questionEl = document.getElementById("study-question");
const answerEl = document.getElementById("study-answer");
const showAnswerBtn = document.getElementById("show-answer-btn");
const nextBtn = document.getElementById("next-btn");
const progressFill = document.getElementById("progress-fill");
const progressText = document.getElementById("progress-text");

function showError(message) {
  loadingEl.classList.add("hidden");
  errorEl.textContent = message;
  errorEl.classList.remove("hidden");
}

async function loadCards() {
  try {
    const deck = await apiFetch(`/decks/${encodeURIComponent(deckId)}`);
    document.getElementById("study-deck-title").textContent = deck.title;
    document.title = `Studying: ${deck.title}`;

    cards = deck.cards || [];
    loadingEl.classList.add("hidden");

    if (cards.length === 0) {
      emptyEl.classList.remove("hidden");
      return;
    }
    startSession();
  } catch (err) {
    if (err.status === 404) {
      showError("This deck isn't available. It may have been deleted, or it belongs to another account.");
    } else {
      showError(err.message);
    }
  }
}

function startSession() {
  currentIndex = 0;
  completeEl.classList.add("hidden");
  contentEl.classList.remove("hidden");
  renderCurrentCard();
}

function renderCurrentCard() {
  const card = cards[currentIndex];
  questionEl.textContent = card.question;
  answerEl.textContent = card.answer;

  cardInner.classList.remove("flipped");
  showAnswerBtn.classList.remove("hidden");
  showAnswerBtn.disabled = false;
  nextBtn.classList.add("hidden");
  answerShown = false;

  progressText.textContent = `${currentIndex + 1} / ${cards.length}`;
  progressFill.style.width = `${(currentIndex / cards.length) * 100}%`;
}

function revealAnswer() {
  cardInner.classList.add("flipped");
  showAnswerBtn.classList.add("hidden");
  nextBtn.classList.remove("hidden");
  answerShown = true;
}

function goToNext() {
  // Flip the card back to its front face -- like turning to the next one --
  // then swap the content in once that motion has finished.
  nextBtn.disabled = true;
  cardInner.classList.remove("flipped");

  setTimeout(() => {
    currentIndex++;
    if (currentIndex >= cards.length) {
      finishSession();
    } else {
      renderCurrentCard();
    }
    nextBtn.disabled = false;
  }, FLIP_BACK_MS);
}

function finishSession() {
  contentEl.classList.add("hidden");
  completeEl.classList.remove("hidden");
  progressFill.style.width = "100%";
  document.getElementById("study-complete-summary").textContent =
    `You reviewed ${cards.length} card${cards.length === 1 ? "" : "s"}.`;
}

showAnswerBtn.addEventListener("click", revealAnswer);
nextBtn.addEventListener("click", goToNext);
document.getElementById("restart-btn").addEventListener("click", startSession);

// Let students use the keyboard (space / enter) to move faster on desktop.
document.addEventListener("keydown", (event) => {
  if (contentEl.classList.contains("hidden")) return;
  if (event.code === "Space" || event.code === "Enter") {
    event.preventDefault();
    if (!answerShown) {
      revealAnswer();
    } else if (!nextBtn.disabled) {
      goToNext();
    }
  }
});

loadCards();
