"use strict";
(() => {
  const key = 'bttf-theme';
  const root = document.documentElement;
  const icons = {
    dark: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 13A8.5 8.5 0 0 1 11 3.5 8.5 8.5 0 1 0 20.5 13Z"/></svg>',
    light: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/></svg>',
  };
  let initial = 'light';
  try { if (localStorage.getItem(key) === 'dark') initial = 'dark'; } catch {}
  function apply(theme) {
    root.dataset.theme = theme;
    const favicon = document.getElementById('site-icon');
    if (favicon) {
      const url = new URL(favicon.getAttribute('href'), document.baseURI);
      url.pathname = url.pathname.replace(/favicon-(?:light|dark)\.svg$/, 'favicon-' + theme + '.svg');
      favicon.href = url.href;
    }
    const button = document.getElementById('theme-toggle');
    if (!button) return;
    const next = theme === 'dark' ? 'light' : 'dark';
    const label = next === 'dark' ? 'Dark' : 'Light';
    button.innerHTML = icons[next] + '<span>' + label + '</span>';
    button.title = 'Switch to ' + next + ' theme';
    button.setAttribute('aria-label', button.title);
    button.setAttribute('aria-pressed', String(theme === 'dark'));
  }
  // Apply the saved palette before the stylesheet paints the page.
  apply(initial);
  document.addEventListener('DOMContentLoaded', () => {
    apply(root.dataset.theme);
    document.getElementById('theme-toggle')?.addEventListener('click', () => {
      const theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      apply(theme);
      try { localStorage.setItem(key, theme); } catch {}
    });
  });
  window.addEventListener('storage', event => {
    if (event.key === key) apply(event.newValue === 'dark' ? 'dark' : 'light');
  });
})();
