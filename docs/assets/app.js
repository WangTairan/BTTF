
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

function updateResultMatrixBest(matrix) {
  const links = Array.from(matrix.querySelectorAll(".result-link[data-score][data-dataset]"));
  links.forEach((link) => link.classList.remove("best"));
  const bestByDataset = new Map();
  links.forEach((link) => {
    const row = link.closest("tr");
    if (row && row.hidden) return;
    const score = Number(link.dataset.score);
    if (!Number.isFinite(score)) return;
    const dataset = link.dataset.dataset;
    const current = bestByDataset.get(dataset);
    if (!current || score > current.score) {
      bestByDataset.set(dataset, { score, link });
    }
  });
  bestByDataset.forEach((item) => item.link.classList.add("best"));
}

function toggleMethodFilter(button) {
  const group = button.dataset.methodGroup;
  const panel = button.closest(".panel");
  if (!group || !panel) return;
  const matrix = panel.querySelector("[data-result-matrix]");
  if (!matrix) return;
  const nextActive = button.getAttribute("aria-pressed") !== "true";
  button.setAttribute("aria-pressed", nextActive ? "true" : "false");
  button.classList.toggle("active", nextActive);
  matrix.querySelectorAll(`tr[data-method-group="${CSS.escape(group)}"]`).forEach((row) => {
    row.hidden = !nextActive;
  });
  updateResultMatrixBest(matrix);
}

function initializeResultMatrices() {
  document.querySelectorAll("[data-result-matrix]").forEach((matrix) => updateResultMatrixBest(matrix));
}

function updatePairFilters(filters) {
  const panel = filters.closest(".panel");
  if (!panel) return;
  const selected = filters.querySelector('[data-pair-category][aria-pressed="true"]');
  const category = selected ? selected.dataset.pairCategory : "all";
  const changedButton = filters.querySelector("[data-changed-only]");
  const changedOnly = changedButton && changedButton.getAttribute("aria-pressed") === "true";
  panel.querySelectorAll("[data-pair-row]").forEach((row) => {
    const categoryMatch = category === "all" || row.dataset.category === category;
    const changedMatch = !changedOnly || row.dataset.changed === "true";
    row.hidden = !(categoryMatch && changedMatch);
  });
}

function selectPairCategory(button) {
  const filters = button.closest("[data-pair-filters]");
  if (!filters) return;
  filters.querySelectorAll("[data-pair-category]").forEach((item) => {
    const active = item === button;
    item.setAttribute("aria-pressed", active ? "true" : "false");
    item.classList.toggle("active", active);
  });
  updatePairFilters(filters);
}

function toggleChangedPairs(button) {
  const filters = button.closest("[data-pair-filters]");
  if (!filters) return;
  const active = button.getAttribute("aria-pressed") !== "true";
  button.setAttribute("aria-pressed", active ? "true" : "false");
  button.classList.toggle("active", active);
  updatePairFilters(filters);
}

function dragInsertBefore(container, dragging, target, clientX) {
  if (!container || !dragging || !target || dragging === target) return;
  const box = target.getBoundingClientRect();
  const after = clientX > box.left + box.width / 2;
  container.insertBefore(dragging, after ? target.nextSibling : target);
}

function syncMatrixOrderFromFilters(filters) {
  const panel = filters.closest(".panel");
  const matrix = panel ? panel.querySelector("[data-result-matrix]") : null;
  const tbody = matrix ? matrix.querySelector("tbody") : null;
  if (!tbody) return;
  filters.querySelectorAll(".method-filter[data-method-group]").forEach((button) => {
    const group = button.dataset.methodGroup;
    const row = tbody.querySelector(`tr[data-method-group="${CSS.escape(group)}"]`);
    if (row) tbody.appendChild(row);
  });
  updateResultMatrixBest(matrix);
}

document.addEventListener("click", (event) => {
  const pairCategory = event.target.closest("[data-pair-category]");
  if (pairCategory) {
    selectPairCategory(pairCategory);
    return;
  }
  const changedOnly = event.target.closest("[data-changed-only]");
  if (changedOnly) {
    toggleChangedPairs(changedOnly);
    return;
  }
  const methodFilter = event.target.closest(".method-filter[data-method-group]");
  if (methodFilter) {
    if (methodFilter.dataset.dragJustEnded === "true") {
      delete methodFilter.dataset.dragJustEnded;
      return;
    }
    toggleMethodFilter(methodFilter);
    return;
  }
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

document.addEventListener("dragstart", (event) => {
  const button = event.target.closest ? event.target.closest('.method-filter[draggable="true"][data-method-group]') : null;
  if (!button) return;
  button.classList.add("dragging");
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", button.dataset.methodGroup || "");
  }
});

document.addEventListener("dragover", (event) => {
  const target = event.target.closest ? event.target.closest('.method-filter[draggable="true"][data-method-group]') : null;
  if (!target) return;
  const filters = target.parentElement;
  const dragging = filters ? filters.querySelector(".method-filter.dragging") : null;
  if (!dragging) return;
  event.preventDefault();
  dragInsertBefore(filters, dragging, target, event.clientX);
  syncMatrixOrderFromFilters(filters);
});

document.addEventListener("dragend", (event) => {
  const button = event.target.closest ? event.target.closest(".method-filter.dragging") : null;
  if (!button) return;
  const filters = button.closest("[data-method-filters]");
  button.classList.remove("dragging");
  button.dataset.dragJustEnded = "true";
  window.setTimeout(() => {
    delete button.dataset.dragJustEnded;
  }, 0);
  if (filters) syncMatrixOrderFromFilters(filters);
});

document.addEventListener("toggle", (event) => {
  const detail = event.target.closest ? event.target.closest(".mask-detail") : null;
  if (!detail) return;
  highlightMaskLines(detail);
}, true);

document.addEventListener("DOMContentLoaded", initializeResultMatrices);
