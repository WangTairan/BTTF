
function numericValue(row, key) {
  const raw = row.getAttribute(`data-${key}`) || "";
  if (raw === "") return null;
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

function sortSampleTable(control) {
  const table = control.closest("table");
  if (!table) return;
  const tbody = table.querySelector("tbody");
  const key = control.dataset.sortKey;
  const current = control.dataset.sortDir || "desc";
  const dir = current === "desc" ? -1 : 1;
  const rows = Array.from(tbody.querySelectorAll("tr"));
  rows.sort((left, right) => {
    const a = numericValue(left, key);
    const b = numericValue(right, key);
    if (a === null && b === null) {
      return numericValue(left, "order") - numericValue(right, "order");
    }
    if (a === null) return 1;
    if (b === null) return -1;
    if (a === b) return numericValue(left, "order") - numericValue(right, "order");
    return (a - b) * dir;
  });
  rows.forEach((row) => tbody.appendChild(row));
  table.querySelectorAll(".sort-header").forEach((item) => {
    item.classList.remove("active");
    const marker = item.querySelector("span");
    if (marker) marker.textContent = "↕";
  });
  const indicator = control.querySelector("span");
  if (indicator) indicator.textContent = current === "desc" ? "↓" : "↑";
  control.classList.add("active");
  control.dataset.sortDir = current === "desc" ? "asc" : "desc";
}

function clearSourceHighlights(panel) {
  panel.querySelectorAll(".source-line.active").forEach((line) => {
    line.classList.remove("active", "recovery-good", "recovery-mid", "recovery-bad", "recovery-missing");
  });
}

function highlightMaskLines(detail) {
  const panel = detail.closest(".mode-panel");
  if (!panel) return;
  clearSourceHighlights(panel);
  if (!detail.open) return;
  const status = detail.dataset.status || "recovery-missing";
  const lines = (detail.dataset.lines || "").split(",").filter(Boolean);
  let first = null;
  lines.forEach((lineIndex) => {
    const line = panel.querySelector(`.source-line[data-line="${lineIndex}"]`);
    if (!line) return;
    line.classList.add("active", status);
    if (!first) first = line;
  });
  if (first) {
    first.scrollIntoView({ block: "nearest" });
  }
}

function sortPatchCards(button) {
  const panel = button.closest(".mode-panel");
  if (!panel) return;
  const cards = Array.from(panel.querySelectorAll(".patch-card[data-score]"));
  if (!cards.length) return;
  const target = button.dataset.sortDir || "desc";
  const dir = target === "asc" ? 1 : -1;
  cards.sort((left, right) => {
    const a = Number(left.dataset.score);
    const b = Number(right.dataset.score);
    if (!Number.isFinite(a) && !Number.isFinite(b)) return 0;
    if (!Number.isFinite(a)) return 1;
    if (!Number.isFinite(b)) return -1;
    return (a - b) * dir;
  });
  cards.forEach((card) => card.parentElement.appendChild(card));
  const next = target === "asc" ? "desc" : "asc";
  button.dataset.sortDir = next;
  button.firstChild.textContent = target === "asc" ? "Worst first " : "Best first ";
  const marker = button.querySelector("span");
  if (marker) marker.textContent = target === "asc" ? "↓" : "↑";
}

document.addEventListener("click", (event) => {
  const patchSort = event.target.closest(".patch-sort");
  if (patchSort) {
    sortPatchCards(patchSort);
    return;
  }
  const button = event.target.closest(".sort-header[data-sort-key]");
  if (button) {
    sortSampleTable(button);
    return;
  }
  const tab = event.target.closest(".mode-tab[data-mode-target]");
  if (!tab) return;
  const panel = tab.closest(".panel");
  panel.querySelectorAll(".mode-tab").forEach((item) => item.classList.remove("active"));
  panel.querySelectorAll(".mode-panel").forEach((item) => item.classList.remove("active"));
  tab.classList.add("active");
  const target = document.getElementById(tab.dataset.modeTarget);
  if (target) target.classList.add("active");
});

document.addEventListener("toggle", (event) => {
  const detail = event.target.closest ? event.target.closest(".mask-detail") : null;
  if (!detail) return;
  highlightMaskLines(detail);
}, true);
