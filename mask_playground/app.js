const editor = document.querySelector("#source-editor");
const codeHighlight = document.querySelector("#code-highlight");
const lineNumbers = document.querySelector("#line-numbers");
const datasetSelect = document.querySelector("#dataset-select");
const sampleSelect = document.querySelector("#sample-select");
const languageDisplay = document.querySelector("#language-display");
const modelSelect = document.querySelector("#model-select");
const templateSelect = document.querySelector("#template-select");
const runButton = document.querySelector("#run-button");
const selectionStatus = document.querySelector("#selection-status");
const sourceStats = document.querySelector("#source-stats");
const maskStats = document.querySelector("#mask-stats");
const promptSystem = document.querySelector("#prompt-system");
const promptExamples = document.querySelector("#prompt-examples");
const promptMask = document.querySelector("#prompt-mask");
const responseOutput = document.querySelector("#response-output");
const resultMeta = document.querySelector("#result-meta");
const toast = document.querySelector("#toast");

const KEYWORDS = {
  java: new Set("abstract assert boolean break byte case catch char class const continue default do double else enum extends final finally float for goto if implements import instanceof int interface long native new package private protected public return short static strictfp super switch synchronized this throw throws transient try void volatile while true false null record sealed permits var".split(" ")),
  python: new Set("and as assert async await break class continue def del elif else except False finally for from global if import in is lambda None nonlocal not or pass raise return True try while with yield match case".split(" ")),
  cuda: new Set("alignas alignof asm auto bool break case catch char class const constexpr continue default delete do double else enum explicit export extern false float for friend goto if inline int long mutable namespace new noexcept nullptr operator private protected public register reinterpret_cast return short signed sizeof static static_assert struct switch template this thread_local throw true try typedef typeid typename union unsigned using virtual void volatile wchar_t while __global__ __device__ __host__ __shared__ __constant__ __managed__ __restrict__ __syncthreads dim3".split(" ")),
};

const PROMPT_CACHE_PREFIX = "mask-playground-prompt:";

let selection = { start: 0, end: 0 };
let previewTimer = null;
let currentMaskSection = "";
let activePromptTab = "all";
let currentLanguage = "java";
let response = { extracted: "No response.", completed: "No response.", raw: "No response." };
let activeResponseTab = "extracted";

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function highlightCode(code, language = currentLanguage) {
  const keywords = KEYWORDS[language] || KEYWORDS.java;
  const tokenPattern = /("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\/\/[^\n]*|\/\*[\s\S]*?\*\/|#[^\n]*|\b\d+(?:\.\d+)?\b|\b[A-Za-z_]\w*\b)/g;
  let html = "";
  let cursor = 0;
  for (const match of code.matchAll(tokenPattern)) {
    html += escapeHtml(code.slice(cursor, match.index));
    const token = match[0];
    let tokenClass = "identifier";
    if (token.startsWith("//") || token.startsWith("/*") || token.startsWith("#")) tokenClass = "comment";
    else if (token.startsWith('"') || token.startsWith("'")) tokenClass = "string";
    else if (/^\d/.test(token)) tokenClass = "number";
    else if (keywords.has(token)) tokenClass = "keyword";
    html += `<span class="syntax-${tokenClass}">${escapeHtml(token)}</span>`;
    cursor = match.index + token.length;
  }
  return html + escapeHtml(code.slice(cursor));
}

function renderSourceHighlight() {
  const code = editor.value;
  if (selection.end > selection.start) {
    codeHighlight.innerHTML = `${highlightCode(code.slice(0, selection.start))}<mark>${highlightCode(code.slice(selection.start, selection.end))}</mark>${highlightCode(code.slice(selection.end))}`;
  } else {
    codeHighlight.innerHTML = highlightCode(code);
  }
  if (code.endsWith("\n")) codeHighlight.innerHTML += " ";
}

function selectedPayload(includeCustomPrompt = false) {
  const code = editor.value;
  const payload = {
    prefix: code.slice(0, selection.start),
    selected: code.slice(selection.start, selection.end),
    suffix: code.slice(selection.end),
    model: modelSelect.value,
    prompt_variant: activePromptVariant(),
  };
  if (includeCustomPrompt) {
    payload.custom_prompt = `${promptSystem.value}${promptExamples.value}${currentMaskSection}`;
  }
  return payload;
}

function lineAt(offset) {
  return editor.value.slice(0, offset).split("\n").length;
}

function updateEditorChrome() {
  const lines = Math.max(1, editor.value.split("\n").length);
  lineNumbers.textContent = Array.from({ length: lines }, (_, index) => index + 1).join("\n");
  sourceStats.textContent = `${lines} lines · ${editor.value.length} characters`;
  if (selection.end > selection.start) {
    const startLine = lineAt(selection.start);
    const endLine = lineAt(selection.end);
    const lineLabel = startLine === endLine ? `Line ${startLine}` : `Lines ${startLine}–${endLine}`;
    const count = selection.end - selection.start;
    selectionStatus.textContent = `${lineLabel} · ${count} chars`;
    selectionStatus.classList.add("active");
    maskStats.textContent = `${count} characters selected`;
    runButton.disabled = false;
  } else {
    selectionStatus.textContent = "No selection";
    selectionStatus.classList.remove("active");
    maskStats.textContent = "Mask not set";
    runButton.disabled = true;
  }
  renderSourceHighlight();
}

function captureSelection() {
  selection = { start: editor.selectionStart, end: editor.selectionEnd };
  updateEditorChrome();
  schedulePreview();
}

function promptCacheKey(variant = templateSelect.value) {
  return `${PROMPT_CACHE_PREFIX}${variant.replace(/__custom$/, "")}`;
}

function activePromptVariant() {
  return templateSelect.value.replace(/__custom$/, "");
}

function isCustomPromptSlot() {
  return templateSelect.value.endsWith("__custom");
}

function templateLabel() {
  return templateSelect.options[templateSelect.selectedIndex]?.textContent || templateSelect.value;
}

async function refreshPreview() {
  if (selection.end <= selection.start || !modelSelect.value) {
    currentMaskSection = "";
    promptSystem.value = "";
    promptExamples.value = "";
    renderPromptViews();
    return;
  }
  try {
    const data = await postJson("/api/prompt", selectedPayload());
    if (typeof data.mask_section !== "string") {
      throw new Error("The lab server is out of date. Restart mask_playground.server.");
    }
    currentMaskSection = data.mask_section;
    let cachedSections = isCustomPromptSlot()
      ? window.localStorage.getItem(promptCacheKey())
      : null;
    if (cachedSections) {
      try {
        cachedSections = JSON.parse(cachedSections);
      } catch {
        cachedSections = { system: cachedSections, examples: data.examples };
      }
    }
    promptSystem.value = cachedSections?.system ?? data.system_prompt;
    promptExamples.value = cachedSections?.examples ?? data.examples;
    renderPromptViews();
  } catch (error) {
    showError(error.message);
  }
}

function renderPromptViews() {
  document.querySelector("#prompt-all-system").textContent = promptSystem.value;
  const allExamples = document.querySelector("#prompt-all-examples");
  allExamples.textContent = promptExamples.value;
  allExamples.hidden = !promptExamples.value;
  document.querySelector("#prompt-all-mask").innerHTML = currentMaskSection
    ? highlightCode(currentMaskSection)
    : "Select a source region.";
  promptMask.innerHTML = currentMaskSection
    ? highlightCode(currentMaskSection)
    : "Select a source region.";
  document.querySelectorAll("[data-prompt-view]").forEach((view) => {
    view.hidden = view.dataset.promptView !== activePromptTab;
  });
}

function savePromptSections() {
  if (!isCustomPromptSlot()) templateSelect.value = `${activePromptVariant()}__custom`;
  window.localStorage.setItem(promptCacheKey(), JSON.stringify({
    system: promptSystem.value,
    examples: promptExamples.value,
  }));
  renderPromptViews();
}

function schedulePreview() {
  window.clearTimeout(previewTimer);
  previewTimer = window.setTimeout(refreshPreview, 160);
}

async function runRecovery() {
  if (selection.end <= selection.start) return;
  runButton.disabled = true;
  runButton.querySelector(".run-icon").textContent = "■";
  resultMeta.innerHTML = "<span>Running</span>";
  response = {
    extracted: "Waiting for model response…",
    completed: "Waiting for model response…",
    raw: "Waiting for model response…",
  };
  renderResponse();
  try {
    const data = await postJson("/api/recover", selectedPayload(true));
    response.extracted = data.extracted_response || "No mask value extracted.";
    response.completed = data.completed_code || "No completed code available.";
    response.raw = data.raw_response || "Empty response.";
    const stateClass = data.extraction_failed || data.recovered_mask_count !== 1 ? "error" : "ok";
    const similarities = data.similarities || { sequence: data.similarity };
    const similarityLabels = {
      exact: "Exact",
      sequence: "Sequence",
      jaccard: "Token Jaccard",
      cosine: "Token cosine",
      bleu: "BLEU",
    };
    resultMeta.innerHTML = [
      `<span class="${stateClass}">${stateClass === "ok" ? "JSON extracted" : "Extraction issue"}</span>`,
      `<span>${data.elapsed_ms} ms</span>`,
      `<span>${data.recovered_mask_count} mask value</span>`,
      ...Object.entries(similarities).map(([name, value]) =>
        `<span>${similarityLabels[name] || name} ${Number(value).toFixed(4)}</span>`
      ),
    ].join("");
    renderResponse();
  } catch (error) {
    response = { extracted: "Recovery failed.", completed: "Recovery failed.", raw: error.message };
    resultMeta.innerHTML = `<span class="error">Failed</span><span>${escapeHtml(error.message)}</span>`;
    renderResponse();
    showError(error.message);
  } finally {
    runButton.querySelector(".run-icon").textContent = "▶";
    runButton.disabled = selection.end <= selection.start;
  }
}

function renderResponse() {
  const value = response[activeResponseTab];
  if (activeResponseTab === "raw") responseOutput.textContent = value;
  else responseOutput.innerHTML = highlightCode(value);
}

async function postJson(url, payload) {
  const request = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await request.json();
  if (!request.ok) throw new Error(data.error || `Request failed: ${request.status}`);
  return data;
}

function showError(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  window.setTimeout(() => toast.classList.remove("visible"), 4000);
}

async function loadConfig() {
  const request = await fetch("/api/config");
  const config = await request.json();
  modelSelect.innerHTML = config.models
    .map((model) => `<option value="${model.key}">${model.label} · ${model.provider}</option>`)
    .join("");
  modelSelect.value = config.models.some((model) => model.key === "gpt41-nano") ? "gpt41-nano" : config.models[0]?.key;
  templateSelect.innerHTML = config.prompt_templates
    .flatMap((template) => [
      `<option value="${template.key}">${template.label}</option>`,
      `<option value="${template.key}__custom">${template.label} · custom</option>`,
    ])
    .join("");
  templateSelect.value = "original";
}

async function loadDatasets() {
  const request = await fetch("/api/datasets");
  const data = await request.json();
  if (!request.ok) throw new Error(data.error || "Failed to load datasets.");
  datasetSelect.innerHTML = data.datasets
    .map((dataset) => `<option value="${dataset.key}">${dataset.label} · ${dataset.count}</option>`)
    .join("");
  datasetSelect.value = data.datasets.some((dataset) => dataset.key === "scalabrino")
    ? "scalabrino"
    : data.datasets[0]?.key;
  await loadSamples(datasetSelect.value);
}

async function loadSamples(datasetKey) {
  const request = await fetch(`/api/dataset?dataset=${encodeURIComponent(datasetKey)}`);
  const data = await request.json();
  if (!request.ok) throw new Error(data.error || "Failed to load dataset samples.");
  sampleSelect.innerHTML = data.samples
    .map((sample) => `<option value="${sample.id}">${sample.id}</option>`)
    .join("");
  const preferred = datasetKey === "scalabrino" && data.samples.some((sample) => sample.id === "Scalabrio152")
    ? "Scalabrio152"
    : data.samples[0]?.id;
  sampleSelect.value = preferred;
  await loadSample(datasetKey, preferred);
}

async function loadSample(datasetKey, sampleId) {
  if (!sampleId) return;
  const request = await fetch(`/api/dataset?dataset=${encodeURIComponent(datasetKey)}&id=${encodeURIComponent(sampleId)}`);
  const data = await request.json();
  if (!request.ok) throw new Error(data.error || "Failed to load dataset sample.");
  editor.value = data.code;
  editor.setSelectionRange(0, 0);
  selection = { start: 0, end: 0 };
  currentLanguage = data.language;
  languageDisplay.textContent = data.language === "cuda" ? "CUDA" : data.language[0].toUpperCase() + data.language.slice(1);
  response = { extracted: "No response.", completed: "No response.", raw: "No response." };
  const datasetLabel = datasetSelect.options[datasetSelect.selectedIndex]?.textContent.split(" · ")[0] || datasetKey;
  resultMeta.innerHTML = `<span>${escapeHtml(datasetLabel)}</span><span>${escapeHtml(data.id)}</span><span>${escapeHtml(languageDisplay.textContent)}</span>`;
  renderResponse();
  updateEditorChrome();
  await refreshPreview();
}

function syncEditorScroll() {
  lineNumbers.scrollTop = editor.scrollTop;
  codeHighlight.scrollTop = editor.scrollTop;
  codeHighlight.scrollLeft = editor.scrollLeft;
}

function installSplitter(splitter, orientation) {
  splitter.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    splitter.setPointerCapture(event.pointerId);
    document.body.classList.add("resizing");
  });
  splitter.addEventListener("pointermove", (event) => {
    if (!splitter.hasPointerCapture(event.pointerId)) return;
    if (orientation === "vertical") {
      const workspace = document.querySelector(".workspace");
      const rect = workspace.getBoundingClientRect();
      const width = Math.max(360, Math.min(rect.width - 366, event.clientX - rect.left));
      workspace.style.setProperty("--source-width", `${width}px`);
    } else {
      const column = document.querySelector(".right-column");
      const rect = column.getBoundingClientRect();
      const height = Math.max(170, Math.min(rect.height - 176, event.clientY - rect.top));
      column.style.setProperty("--prompt-height", `${height}px`);
    }
  });
  const stop = (event) => {
    if (splitter.hasPointerCapture(event.pointerId)) splitter.releasePointerCapture(event.pointerId);
    document.body.classList.remove("resizing");
  };
  splitter.addEventListener("pointerup", stop);
  splitter.addEventListener("pointercancel", stop);
}

editor.addEventListener("select", captureSelection);
editor.addEventListener("mouseup", captureSelection);
editor.addEventListener("keyup", captureSelection);
editor.addEventListener("input", () => {
  selection = { start: editor.selectionStart, end: editor.selectionEnd };
  updateEditorChrome();
  schedulePreview();
});
editor.addEventListener("scroll", syncEditorScroll);
datasetSelect.addEventListener("change", () => {
  loadSamples(datasetSelect.value).catch((error) => showError(error.message));
});
sampleSelect.addEventListener("change", () => {
  loadSample(datasetSelect.value, sampleSelect.value).catch((error) => showError(error.message));
});
templateSelect.addEventListener("change", refreshPreview);
promptSystem.addEventListener("input", savePromptSections);
promptExamples.addEventListener("input", savePromptSections);
document.querySelectorAll("[data-prompt-tab]").forEach((button) => {
  button.addEventListener("click", () => {
    activePromptTab = button.dataset.promptTab;
    document.querySelectorAll("[data-prompt-tab]").forEach((tab) => tab.classList.toggle("active", tab === button));
    renderPromptViews();
  });
});
runButton.addEventListener("click", runRecovery);
document.querySelectorAll("[data-response-tab]").forEach((button) => {
  button.addEventListener("click", () => {
    activeResponseTab = button.dataset.responseTab;
    document.querySelectorAll("[data-response-tab]").forEach((tab) => tab.classList.toggle("active", tab === button));
    renderResponse();
  });
});

installSplitter(document.querySelector("#splitter-vertical"), "vertical");
installSplitter(document.querySelector("#splitter-horizontal"), "horizontal");

async function initialize() {
  updateEditorChrome();
  try {
    await loadConfig();
    await loadDatasets();
  } catch (error) {
    showError(error.message);
  }
}

initialize();
