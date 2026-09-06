(() => {
  'use strict';
  const wire = document.querySelector('[data-news-wire]');
  const button = wire?.querySelector('[data-wire-toggle]');
  if (!button) return;
  button.hidden = false;
  button.addEventListener('click', () => {
    const paused = button.getAttribute('aria-pressed') !== 'true';
    button.setAttribute('aria-pressed', String(paused));
    button.textContent = paused ? 'Resume wire' : 'Pause wire';
    wire.dataset.paused = String(paused);
  });
})();
