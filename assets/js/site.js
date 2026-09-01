(function () {
  'use strict';

  const header = document.querySelector('.site-header');
  const toggle = document.querySelector('.nav-toggle');
  const navigation = document.getElementById('primary-navigation');

  if (!header || !toggle || !navigation) return;

  toggle.hidden = false;
  header.classList.add('nav-is-ready');

  const setMenuState = (isOpen) => {
    toggle.setAttribute('aria-label', isOpen ? 'Close navigation' : 'Open navigation');
    toggle.setAttribute('aria-expanded', String(isOpen));
    header.classList.toggle('nav-is-open', isOpen);
  };

  toggle.addEventListener('click', () => {
    setMenuState(toggle.getAttribute('aria-expanded') !== 'true');
  });

  navigation.addEventListener('click', (event) => {
    if (event.target.closest('a')) setMenuState(false);
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
      setMenuState(false);
      toggle.focus();
    }
  });

  window.addEventListener('resize', () => {
    if (window.matchMedia('(min-width: 901px)').matches) setMenuState(false);
  });
})();
