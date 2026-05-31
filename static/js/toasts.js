/**
 * toasts.js
 * Auto-initializes and shows all Bootstrap toasts rendered by toasts.html
 */
document.addEventListener('DOMContentLoaded', () => {
  const levelClass = {
    success : 'bg-gradient-success',
    error   : 'bg-gradient-danger',
    warning : 'bg-gradient-warning',
    info    : 'bg-gradient-info',
    debug   : 'bg-gradient-secondary',
  };
  const levelIcon = {
    success : 'check_circle',
    error   : 'error',
    warning : 'warning',
    info    : 'info',
    debug   : 'bug_report',
  };

  document.querySelectorAll('.app-toast').forEach(el => {
    // Determine level from data attribute (Django tags can be multi-word e.g. "messages success")
    const raw   = (el.dataset.level || '').toLowerCase();
    const level = Object.keys(levelClass).find(k => raw.includes(k)) || 'info';

    el.classList.add(levelClass[level], 'text-white');

    // Inject icon into toast body
    const body = el.querySelector('.toast-body');
    if (body) {
      const icon = document.createElement('i');
      icon.className = 'material-symbols-rounded me-2 align-middle';
      icon.style.fontSize = '1.1rem';
      icon.textContent = levelIcon[level] || 'info';
      body.prepend(icon);
    }

    const toast = new bootstrap.Toast(el, {
      autohide : level !== 'error',
      delay    : level === 'error' ? 0 : 5000,
    });
    toast.show();
  });
});

/**
 * showToast(message, level)
 * Programmatically trigger a toast from JavaScript.
 * level: 'success' | 'error' | 'warning' | 'info'
 */
function showToast(message, level = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const levelClass = {
    success : 'bg-gradient-success',
    error   : 'bg-gradient-danger',
    warning : 'bg-gradient-warning',
    info    : 'bg-gradient-info',
  };
  const levelIcon = {
    success : 'check_circle',
    error   : 'error',
    warning : 'warning',
    info    : 'info',
  };

  const el = document.createElement('div');
  el.className = `toast align-items-center text-white border-0 ${levelClass[level] || 'bg-gradient-info'}`;
  el.setAttribute('role', 'alert');
  el.setAttribute('aria-live', 'assertive');
  el.setAttribute('aria-atomic', 'true');
  el.innerHTML = `
    <div class="d-flex">
      <div class="toast-body d-flex align-items-center gap-2">
        <i class="material-symbols-rounded" style="font-size:1.1rem">${levelIcon[level] || 'info'}</i>
        ${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>`;
  container.appendChild(el);

  const toast = new bootstrap.Toast(el, {
    autohide : level !== 'error',
    delay    : level === 'error' ? 0 : 5000,
  });
  toast.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}
