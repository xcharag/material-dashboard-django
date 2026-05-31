/**
 * page-loader.js
 * – Top progress bar during page navigation
 * – Button loading state on form submit
 * – Page content reveal with skeleton placeholder support
 */
(function () {
  const bar = document.getElementById('topProgressBar');

  /* ── Progress bar helpers ─────────────────────────────────────────── */
  function barStart() {
    if (!bar) return;
    bar.style.width = '0%';
    bar.classList.add('loading');
    // Animate to ~75% quickly then stall waiting for page load
    requestAnimationFrame(() => {
      bar.style.transition = 'width .6s ease';
      bar.style.width = '75%';
    });
  }

  function barFinish() {
    if (!bar) return;
    bar.style.transition = 'width .2s ease, opacity .4s ease .3s';
    bar.style.width = '100%';
    bar.classList.remove('loading');
    setTimeout(() => { bar.style.opacity = '0'; }, 350);
    setTimeout(() => { bar.style.width = '0%'; bar.style.opacity = ''; }, 750);
  }

  /* ── Page content reveal ──────────────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', () => {
    document.body.classList.add('page-loaded');
    barFinish();
  });

  /* ── Intercept navigation clicks ─────────────────────────────────── */
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href]');
    if (!link) return;
    const href = link.getAttribute('href');
    // Skip anchors, javascript:, external links, same page
    if (!href || href.startsWith('#') || href.startsWith('javascript') ||
        href.startsWith('mailto') || link.target === '_blank') return;
    // Skip data-bs-* toggle links (Bootstrap components)
    if (link.hasAttribute('data-bs-toggle') || link.hasAttribute('data-bs-dismiss')) return;
    barStart();
  });

  /* ── Form submit → button loading state ──────────────────────────── */
  document.addEventListener('submit', (e) => {
    const form = e.target;
    const btn = form.querySelector('[type="submit"]');
    if (!btn) return;
    barStart();
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML =
      '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Guardando…';
    // Safety restore in case navigation is cancelled
    setTimeout(() => {
      btn.disabled = false;
      btn.innerHTML = original;
    }, 12000);
  });
})();
