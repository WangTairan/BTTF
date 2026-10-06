
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
  const previous = table.dataset.activeSortKey === key ? table.dataset.activeSortDir : "none";
  const states = control.hasAttribute('data-gap-key')
    ? ['none', 'asc', 'desc', 'gap-asc', 'gap-desc'] : ['none', 'asc', 'desc'];
  const current = states[(states.indexOf(previous) + 1) % states.length];
  const gap = current.startsWith('gap-');
  const valueKey = gap ? control.dataset.gapKey : key;
  const dir = current.endsWith("desc") ? -1 : 1;
  const rows = Array.from(tbody.querySelectorAll("tr"));
  rows.sort((left, right) => {
    if (current === "none") return numericValue(left, "order") - numericValue(right, "order");
    const a = numericValue(left, valueKey);
    const b = numericValue(right, valueKey);
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
    if (!item.dataset.originalTitle) item.dataset.originalTitle = item.title || item.textContent.trim();
    item.title = item.dataset.originalTitle;
    item.closest("th")?.setAttribute("aria-sort", "none");
  });
  const indicator = control.querySelector("span");
  if (current !== "none") {
    const direction = dir < 0 ? '↓' : '↑';
    if (indicator) indicator.textContent = (gap ? 'Δ' : '') + direction;
    control.title = gap ? `Human percentile gap: ${dir < 0 ? 'largest first' : 'smallest first'}` : `Score: ${dir < 0 ? 'descending' : 'ascending'}`;
    control.classList.add("active");
    control.closest("th")?.setAttribute("aria-sort", gap ? 'other' : dir < 0 ? "descending" : "ascending");
  }
  table.dataset.activeSortKey = current === "none" ? "" : key;
  table.dataset.activeSortDir = current;
}

function updateResultMatrixBest(matrix) {
  const links = Array.from(matrix.querySelectorAll(".result-link[data-score][data-dataset]"));
  links.forEach((link) => link.classList.remove("best"));
  const bestByDataset = new Map();
  links.forEach((link) => {
    const row = link.closest("tr");
    if ((row && row.hidden) || link.closest("td")?.hidden) return;
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

function initializeResultMatrices() {
  document.querySelectorAll("[data-result-matrix]").forEach((matrix) => updateResultMatrixBest(matrix));
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
  panel.querySelector(".method-views")?.classList.toggle("bttf-view", tab.dataset.modeTarget === "mode-bttf");
});


document.addEventListener("change", event => {
  const input = event.target;
  if (input.matches('input[name="explanation-model"]')) {
    document.querySelectorAll('[data-explanation-model]').forEach(panel => panel.hidden = panel.dataset.explanationModel !== input.value);
    return;
  }
  if (input.matches("[data-method-filter]")) {
    document.querySelectorAll('[data-method-filter="'+CSS.escape(input.dataset.methodFilter)+'"]').forEach(control=>control.checked=input.checked);
    document.querySelectorAll('tr[data-method-group="'+CSS.escape(input.dataset.methodFilter)+'"]').forEach(row=>row.hidden=!input.checked);
  } else if (input.matches("[data-dataset-filter]")) {
    const key=CSS.escape(input.dataset.datasetFilter);
    document.querySelectorAll('[data-dataset-column="'+key+'"], [data-dataset-row="'+key+'"]').forEach(cell=>cell.hidden=!input.checked);
  } else return;
  initializeResultMatrices();
});
document.addEventListener("DOMContentLoaded", initializeResultMatrices);

function initializeCodeCopy() {
  document.querySelectorAll("pre, .diagnostic-code").forEach(code => {
    if (code.hidden || code.dataset.noCodeCopy === "true" || code.closest(".copy-code-frame")) return;
    const frame = document.createElement("div");
    frame.className = "copy-code-frame";
    code.before(frame);
    frame.append(code);
    const button = document.createElement("button");
    button.className = "copy-code-button";
    button.type = "button";
    button.title = "Copy code";
    button.setAttribute("aria-label", "Copy code");
    const copyIcon = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4"/></svg>';
    button.innerHTML = copyIcon;
    let feedbackTimer;
    button.onclick = async () => {
      if (code.dataset.noCodeCopy === "true") return;
      const lines = code.querySelectorAll(".line-text");
      const text = code.dataset.copySource ?? (lines.length ? Array.from(lines, line => line.textContent).join("\n") : code.textContent);
      try {
        await navigator.clipboard.writeText(text);
        button.title = "Copied";
        button.setAttribute("aria-label", "Copied");
        button.classList.add("copied");
        button.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="m5 12 4 4 10-10"/></svg>';
        clearTimeout(feedbackTimer);
        feedbackTimer = setTimeout(() => { button.title = "Copy code"; button.setAttribute("aria-label", "Copy code"); button.classList.remove("copied"); button.innerHTML = copyIcon; }, 1500);
      } catch {
        button.title = "Copy failed; select the code to copy";
      }
    };
    frame.append(button);
  });
}
document.addEventListener("DOMContentLoaded", () => {
  initializeHelpTooltips();
  initializeCodeCopy();
  new MutationObserver(initializeCodeCopy).observe(document.body, {childList: true, subtree: true});
});

// Explicit help popovers also work in embedded browsers without native title tips.
function initializeHelpTooltips() {
  const tip = document.createElement('div');
  tip.className = 'help-tooltip'; tip.id = 'bttf-help-tooltip'; tip.hidden = true;
  tip.setAttribute('role', 'tooltip'); document.body.append(tip);
  let active = null;
  document.querySelectorAll('.help-marker[title]').forEach(button => {
    button.dataset.helpText = button.title; button.removeAttribute('title');
  });
  function hide() {
    if (active) active.removeAttribute('aria-describedby');
    active = null; tip.hidden = true;
  }
  function position() {
    if (!active) return;
    const anchor = active.getBoundingClientRect();
    const box = tip.getBoundingClientRect();
    tip.style.left = Math.max(12, Math.min(anchor.left + anchor.width / 2 - box.width / 2, innerWidth - box.width - 12)) + 'px';
    const below = anchor.bottom + 9;
    tip.style.top = Math.max(12, Math.min(below + box.height <= innerHeight - 12 ? below : anchor.top - box.height - 9, innerHeight - box.height - 12)) + 'px';
  }
  function show(button) {
    if (!button?.dataset.helpText) return;
    if (active !== button) hide();
    active = button; tip.textContent = button.dataset.helpText; tip.hidden = false;
    button.setAttribute('aria-describedby', tip.id); position();
  }
  document.addEventListener('pointerover', event => {
    const button = event.target.closest('.help-marker'); if (button) show(button);
  });
  document.addEventListener('pointerout', event => {
    if (active && active.contains(event.target) && !active.contains(event.relatedTarget) && document.activeElement !== active) hide();
  });
  document.addEventListener('focusin', event => {
    const button = event.target.closest('.help-marker'); if (button) show(button);
  });
  document.addEventListener('focusout', event => {if (event.target === active) hide();});
  document.addEventListener('click', event => {
    const button = event.target.closest('.help-marker'); if (button) show(button); else hide();
  });
  document.addEventListener('keydown', event => {if (event.key === 'Escape') hide();});
  window.addEventListener('resize', position);
  document.addEventListener('scroll', position, true);
}
