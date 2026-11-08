/* ===================================================================
   CPGE Flashcards -- class page
   A teacher sees the join code, the students, and the shared decks.
   A student sees the decks shared with the class and can study them.
   =================================================================== */

requireAuth();

const params = new URLSearchParams(window.location.search);
const classId = params.get("id");
if (!classId) {
  window.location.href = "dashboard.html";
}

let currentClass = null;

const loadingEl = document.getElementById("class-loading");
const loadErrorEl = document.getElementById("class-load-error");
const contentEl = document.getElementById("class-content");
const nameEl = document.getElementById("class-name");
const metaEl = document.getElementById("class-meta");
const leaveBtn = document.getElementById("leave-class-btn");
const deleteBtn = document.getElementById("delete-class-btn");
const joinCodeBox = document.getElementById("join-code-box");
const joinCodeEl = document.getElementById("join-code-display");
const copyBtn = document.getElementById("copy-code-btn");
const actionErrorEl = document.getElementById("class-action-error");
const sharedCountEl = document.getElementById("shared-count");
const sharedEmptyEl = document.getElementById("shared-empty");
const sharedListEl = document.getElementById("shared-list");
const sharedNoteEl = document.getElementById("shared-note");
const membersPanel = document.getElementById("members-panel");
const memberCountEl = document.getElementById("member-count");
const membersEmptyEl = document.getElementById("members-empty");
const membersListEl = document.getElementById("members-list");
const membersNoteEl = document.getElementById("members-note");

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value == null ? "" : value;
  return div.innerHTML;
}

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  } catch (e) {
    return "";
  }
}

/** "ABCD2345" -> "ABCD-2345": easier to read off a screen. The server accepts either. */
function formatCode(code) {
  return code && code.length > 4 ? `${code.slice(0, 4)}-${code.slice(4)}` : code || "";
}

function plural(n, word) {
  return `${n} ${word}${n === 1 ? "" : "s"}`;
}

function showLoadError(message) {
  loadingEl.classList.add("hidden");
  contentEl.classList.add("hidden");
  loadErrorEl.textContent = message;
  loadErrorEl.classList.remove("hidden");
}

function showActionError(message) {
  actionErrorEl.textContent = message;
  actionErrorEl.classList.remove("hidden");
}

function clearActionError() {
  actionErrorEl.classList.add("hidden");
}

async function loadClass() {
  loadErrorEl.classList.add("hidden");
  try {
    currentClass = await apiFetch(`/classes/${encodeURIComponent(classId)}`);
    loadingEl.classList.add("hidden");
    contentEl.classList.remove("hidden");
    renderHeader();
    await Promise.all([loadSharedDecks(), currentClass.is_owner ? loadMembers() : null]);
  } catch (err) {
    if (err.status === 404) {
      showLoadError("This class isn't available. You may have left it or been removed, or it was deleted.");
    } else {
      showLoadError(err.message);
    }
  }
}

function renderHeader() {
  const owner = currentClass.is_owner;
  document.title = `${currentClass.name} -- CPGE Flashcards`;
  nameEl.textContent = currentClass.name;
  metaEl.textContent = plural(currentClass.member_count, "student");
  joinCodeBox.classList.toggle("hidden", !owner);
  membersPanel.classList.toggle("hidden", !owner);
  deleteBtn.classList.toggle("hidden", !owner);
  leaveBtn.classList.toggle("hidden", owner);
  if (owner) joinCodeEl.textContent = formatCode(currentClass.join_code);
}

/** Re-read the class so the student count stays right after a removal. */
async function refreshClassMeta() {
  currentClass = await apiFetch(`/classes/${encodeURIComponent(classId)}`);
  renderHeader();
}

async function loadSharedDecks() {
  const owner = currentClass.is_owner;
  const data = await apiFetch(`/classes/${encodeURIComponent(classId)}/decks?limit=100`);
  sharedCountEl.textContent = data.total;

  if (data.items.length === 0) {
    sharedEmptyEl.textContent = owner
      ? "No decks shared yet. Open one of your decks and tick this class under \u201cShare with your classes\u201d."
      : "Your teacher hasn't shared any decks with this class yet.";
    sharedEmptyEl.classList.remove("hidden");
    sharedListEl.innerHTML = "";
    sharedNoteEl.classList.add("hidden");
    return;
  }
  sharedEmptyEl.classList.add("hidden");

  sharedListEl.innerHTML = data.items
    .map(
      (deck) => `
    <div class="list-row" data-deck-id="${escapeHtml(deck.id)}">
      <div class="list-row-main">
        <h3>${escapeHtml(deck.title)}</h3>
        ${deck.description ? `<p class="muted">${escapeHtml(deck.description)}</p>` : ""}
        <span class="deck-meta">${plural(deck.card_count, "card")}</span>
      </div>
      <div class="list-row-actions">
        ${
          deck.card_count > 0
            ? `<a class="btn btn-primary btn-sm btn-link" href="study.html?id=${encodeURIComponent(deck.id)}">Study</a>`
            : ""
        }
        <a class="btn btn-secondary btn-sm btn-link" href="deck.html?id=${encodeURIComponent(deck.id)}">${owner ? "Open" : "View"}</a>
        ${
          owner
            ? `<button type="button" class="btn btn-danger btn-sm unshare-btn" data-deck-id="${escapeHtml(deck.id)}">Unshare</button>`
            : ""
        }
      </div>
    </div>
  `
    )
    .join("");

  sharedListEl.querySelectorAll(".unshare-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      clearActionError();
      try {
        await apiFetch(
          `/classes/${encodeURIComponent(classId)}/decks/${encodeURIComponent(btn.dataset.deckId)}`,
          { method: "DELETE" }
        );
        await loadSharedDecks();
      } catch (err) {
        showActionError(err.message);
      }
    });
  });

  if (data.total > data.items.length) {
    sharedNoteEl.textContent = `Showing the first ${data.items.length} of ${data.total} decks.`;
    sharedNoteEl.classList.remove("hidden");
  } else {
    sharedNoteEl.classList.add("hidden");
  }
}

async function loadMembers() {
  const data = await apiFetch(`/classes/${encodeURIComponent(classId)}/members?limit=200`);
  memberCountEl.textContent = data.total;

  if (data.items.length === 0) {
    membersEmptyEl.classList.remove("hidden");
    membersListEl.innerHTML = "";
    membersNoteEl.classList.add("hidden");
    return;
  }
  membersEmptyEl.classList.add("hidden");

  membersListEl.innerHTML = data.items
    .map(
      (m) => `
    <div class="list-row" data-user-id="${escapeHtml(m.id)}">
      <div class="list-row-main">
        <h3>${escapeHtml(m.full_name || m.email)}</h3>
        <span class="deck-meta">${m.full_name ? `${escapeHtml(m.email)} \u00b7 ` : ""}joined ${formatDate(m.joined_at)}</span>
      </div>
      <div class="list-row-actions">
        <button type="button" class="btn btn-danger btn-sm remove-member-btn" data-user-id="${escapeHtml(m.id)}">Remove</button>
      </div>
    </div>
  `
    )
    .join("");

  membersListEl.querySelectorAll(".remove-member-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Remove this student from the class? They will lose access to its decks.")) return;
      clearActionError();
      try {
        await apiFetch(
          `/classes/${encodeURIComponent(classId)}/members/${encodeURIComponent(btn.dataset.userId)}`,
          { method: "DELETE" }
        );
        await Promise.all([loadMembers(), refreshClassMeta()]);
      } catch (err) {
        showActionError(err.message);
      }
    });
  });

  if (data.total > data.items.length) {
    membersNoteEl.textContent = `Showing the first ${data.items.length} of ${data.total} students.`;
    membersNoteEl.classList.remove("hidden");
  } else {
    membersNoteEl.classList.add("hidden");
  }
}

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(joinCodeEl.textContent);
    copyBtn.textContent = "Copied";
  } catch (err) {
    copyBtn.textContent = "Select and copy";
  }
  setTimeout(() => (copyBtn.textContent = "Copy"), 1800);
});

leaveBtn.addEventListener("click", async () => {
  if (!confirm("Leave this class? You will lose access to its decks until you join again.")) return;
  clearActionError();
  try {
    await apiFetch(`/classes/${encodeURIComponent(classId)}/leave`, { method: "POST" });
    window.location.href = "dashboard.html";
  } catch (err) {
    showActionError(err.message);
  }
});

deleteBtn.addEventListener("click", async () => {
  if (!confirm("Delete this class? Students lose access to its shared decks. Your decks are not deleted.")) return;
  clearActionError();
  try {
    await apiFetch(`/classes/${encodeURIComponent(classId)}`, { method: "DELETE" });
    window.location.href = "dashboard.html";
  } catch (err) {
    showActionError(err.message);
  }
});

document.getElementById("logout-btn").addEventListener("click", () => {
  clearToken();
  window.location.href = "index.html";
});

loadClass();