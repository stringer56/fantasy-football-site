(function () {
  'use strict';

  const countdown = document.getElementById('draft-countdown');
  if (!countdown) return;

  const isoDate = countdown.dataset.datetime;
  const season = countdown.dataset.season || 'Current season';
  const completeMessage = countdown.dataset.completeMessage || `${season} draft is complete.`;
  const status = countdown.querySelector('[data-countdown-status]');
  const unitElements = {
    days: countdown.querySelector('[data-countdown-days]'),
    hours: countdown.querySelector('[data-countdown-hours]'),
    minutes: countdown.querySelector('[data-countdown-minutes]'),
    seconds: countdown.querySelector('[data-countdown-seconds]')
  };

  if (!isoDate) {
    countdown.classList.add('is-tba');
    if (status) status.textContent = `${season} Draft Date TBA`;
    return;
  }

  const target = Date.parse(isoDate);
  if (Number.isNaN(target)) {
    countdown.classList.add('is-tba');
    if (status) status.textContent = `${season} Draft Date TBA`;
    return;
  }

  const update = () => {
    const remaining = target - Date.now();
    if (remaining <= 0) {
      countdown.classList.add('is-complete');
      if (status) status.textContent = completeMessage;
      Object.values(unitElements).forEach((element) => {
        if (element) element.textContent = '00';
      });
      return false;
    }

    const days = Math.floor(remaining / 86400000);
    const hours = Math.floor((remaining % 86400000) / 3600000);
    const minutes = Math.floor((remaining % 3600000) / 60000);
    const seconds = Math.floor((remaining % 60000) / 1000);

    if (unitElements.days) unitElements.days.textContent = String(days).padStart(2, '0');
    if (unitElements.hours) unitElements.hours.textContent = String(hours).padStart(2, '0');
    if (unitElements.minutes) unitElements.minutes.textContent = String(minutes).padStart(2, '0');
    if (unitElements.seconds) unitElements.seconds.textContent = String(seconds).padStart(2, '0');
    if (status) status.textContent = `${days} days, ${hours} hours, ${minutes} minutes, and ${seconds} seconds until the ${season} draft.`;
    countdown.setAttribute('aria-label', status ? status.textContent : 'Draft countdown');
    return true;
  };

  if (update()) {
    const timer = window.setInterval(() => {
      if (!update()) window.clearInterval(timer);
    }, 1000);
  }
})();
