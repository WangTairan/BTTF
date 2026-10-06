"use strict";
(() => {
  const MAX_ZIP = 10 * 1024 * 1024, MAX_EXPANDED = 32 * 1024 * 1024;
  const encoder = new TextEncoder(), decoder = new TextDecoder('utf-8', {fatal: true, ignoreBOM: true});
  const bundles = new Map(), manifests = new Map();
  let databasePromise;
  const digest = async text => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', encoder.encode(text))), b => b.toString(16).padStart(2, '0')).join('');
  function database() {
    if (!databasePromise) databasePromise = new Promise((resolve, reject) => {
      const request = indexedDB.open('bttf-local-source-v1', 1);
      request.onupgradeneeded = () => request.result.createObjectStore('datasets');
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(Error('Browser storage is unavailable.'));
    });
    return databasePromise;
  }
  async function storage(mode, dataset, value) {
    const db = await database();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('datasets', mode === 'get' ? 'readonly' : 'readwrite');
      const store = tx.objectStore('datasets');
      const request = mode === 'get' ? store.get(dataset) : mode === 'put' ? store.put(value, dataset) : store.delete(dataset);
      tx.oncomplete = () => resolve(request.result);
      tx.onerror = tx.onabort = () => reject(Error('Could not save local data.'));
    });
  }
  async function parseArchive(bytes, manifest) {
    if (bytes.byteLength > MAX_ZIP) throw Error('Please select the official dataset ZIP (maximum 10 MB).');
    let expanded = 0, entries = 0;
    const files = fflate.unzipSync(new Uint8Array(bytes), {filter: file => {
      if (++entries > 10000) throw Error('Too many files in the ZIP.');
      if (!/\.jsnp$/i.test(file.name)) return false;
      expanded += file.originalSize;
      if (!Number.isFinite(expanded) || expanded > MAX_EXPANDED || file.originalSize > 2 * 1024 * 1024) throw Error('The ZIP is too large to load safely.');
      return true;
    }});
    return matchSources(Object.values(files), manifest);
  }
  async function parseFolder(fileList, manifest) {
    const files = Array.from(fileList);
    if (files.length > 10000) throw Error('Too many files. Select the dataset folder, not a parent directory.');
    const snippets = files.filter(file => /\.jsnp$/i.test(file.name));
    let expanded = 0;
    for (const file of snippets) {
      expanded += file.size;
      if (!Number.isFinite(expanded) || expanded > MAX_EXPANDED || file.size > 2 * 1024 * 1024) throw Error('The selected folder is too large to load safely.');
    }
    async function* buffers() {
      for (const file of snippets) yield new Uint8Array(await file.arrayBuffer());
    }
    return matchSources(buffers(), manifest);
  }
  async function matchSources(buffers, manifest) {
    const expected = new Map();
    manifest.samples.forEach(row => {
      if (!expected.has(row.sha256)) expected.set(row.sha256, []);
      expected.get(row.sha256).push(row.task_id);
    });
    const sources = Object.create(null);
    for await (const data of buffers) {
      let source = decoder.decode(data);
      if (manifest.dataset !== 'dorn') source = source.replace(/\r\n?/g, '\n');
      const hash = await digest(source);
      for (const task of expected.get(hash) || []) sources[task] = source;
    }
    const count = Object.keys(sources).length;
    if (count !== manifest.samples.length) throw Error(`Matched ${count}/${manifest.samples.length} samples. Select this dataset's official ZIP or complete extracted folder; the saved scores require the evaluated source version.`);
    return {revision: manifest.revision, sources};
  }
  async function hydrate(data) {
    if (data.source_visible !== false) return data; // The fixed 30 examples stay unchanged.
    await ready;
    const manifest = manifests.get(data.dataset), bundle = bundles.get(data.dataset);
    if (!manifest || !bundle || bundle.revision !== manifest.revision) return data;
    const row = manifest.samples.find(row => row.task_id === data.task_id);
    const source = bundle.sources[data.task_id];
    if (!row || typeof source !== 'string' || row.sha256 !== data.source_sha256 || await digest(source) !== row.sha256) return data;
    return {...data, source, source_visible: true,
      features: data.features.map(feature => ({...feature, regions: row.regions[feature.key] || []}))};
  }
  async function initialize(control) {
    const dataset = control.dataset.sourceImport, message = control.querySelector('[role="status"]');
    const input = control.querySelector('[data-source-file]'), load = control.querySelector('[data-source-load]'), clear = control.querySelector('[data-source-clear]');
    const folder = control.querySelector('[data-source-folder]'), loadFolder = control.querySelector('[data-source-load-folder]');
    const folderSupported = 'webkitdirectory' in folder;
    loadFolder.hidden = !folderSupported;
    const busy = value => {load.disabled = value; loadFolder.disabled = value; clear.disabled = value || !bundles.has(dataset);};
    let manifest;
    const say = (text, error = false) => {message.textContent = text; message.classList.toggle('error', error);};
    const loaded = saved => {
      bundles.set(dataset, saved); clear.disabled = false;
      say(`${Object.keys(saved.sources).length} samples loaded. Source code is available on sample pages.`);
    };
    busy(true);
    try {
      const response = await fetch(control.dataset.sourceManifestUrl);
      if (!response.ok) throw Error('Could not load the sample index. Refresh and try again.');
      manifest = await response.json();
      if (manifest.schema_version !== 1 || manifest.dataset !== dataset) throw Error('Unsupported sample index.');
      manifests.set(dataset, manifest);
      try {
        const saved = await storage('get', dataset);
        if (saved && saved.revision === manifest.revision && manifest.samples.every(row => typeof saved.sources?.[row.task_id] === 'string')) loaded(saved);
      } catch (_) { say('Files stay in your browser. Local saving is unavailable; imported data will last for this page only.'); }
      busy(false);
    } catch (error) {say(error.message, true);}
    load.onclick = () => input.click();
    loadFolder.onclick = () => folder.click();
    async function importSelection(kind, files) {
      if (!files.length) return;
      busy(true); say('Reading and matching source files…');
      try {
        const file = files[0];
        if (kind === 'zip' && file.size > MAX_ZIP) throw Error('Please select the official dataset ZIP (maximum 10 MB).');
        const saved = kind === 'folder' ? await parseFolder(files, manifest) : await parseArchive(await file.arrayBuffer(), manifest);
        loaded(saved);
        try { await storage('put', dataset, saved); }
        catch (_) { say('Loaded for this page only. Browser storage is unavailable.'); }
        document.dispatchEvent(new CustomEvent('bttf-source-change', {detail: {dataset}}));
      } catch (error) { say(error.message || 'Could not read the selected data.', true); }
      finally {busy(false);}
    }
    input.onchange = () => {
      const files = Array.from(input.files); input.value = ''; return importSelection('zip', files);
    };
    folder.onchange = () => {
      const files = Array.from(folder.files); folder.value = ''; return importSelection('folder', files);
    };
    clear.onclick = async () => {
      try {
        await storage('delete', dataset); bundles.delete(dataset); clear.disabled = true;
        say('Local data cleared. Load a ZIP or folder to restore source code.');
        document.dispatchEvent(new CustomEvent('bttf-source-change', {detail: {dataset}}));
      } catch (error) {say(error.message, true);}
    };
  }
  const ready = Promise.all(Array.from(document.querySelectorAll('[data-source-import]'), initialize));
  window.BTTFSourceImport = {hydrate, ready, parseArchive, parseFolder};
})();
