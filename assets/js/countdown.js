(function(){
  const el = document.getElementById('draft-countdown');
  if(!el) return;
  const iso = el.dataset.datetime;
  if(!iso) { el.textContent = 'Set draft_datetime in _data/league.yml'; return; }

  const tick = () => {
    const end = new Date(iso).getTime();
    const now = Date.now();
    const diff = end - now;
    if (diff <= 0) { el.textContent = 'Draft is live or completed'; return; }
    const d = Math.floor(diff/86400000);
    const h = Math.floor((diff%86400000)/3600000);
    const m = Math.floor((diff%3600000)/60000);
    const s = Math.floor((diff%60000)/1000);
    el.textContent = `${d}d ${h}h ${m}m ${s}s`;
    requestAnimationFrame(()=>setTimeout(tick, 250));
  };
  tick();
})();
