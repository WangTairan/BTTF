
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

document.addEventListener("click", (event) => {
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
