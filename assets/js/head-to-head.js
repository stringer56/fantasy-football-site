(() => {
  const app = document.querySelector("[data-h2h-app]");
  const source = document.getElementById("h2h-data");
  if (!app || !source) return;

  const selectA = app.querySelector("[data-h2h-a]");
  const selectB = app.querySelector("[data-h2h-b]");
  const result = app.querySelector("[data-h2h-result]");
  const baseurl = app.dataset.baseurl || "";
  let payload;
  try { payload = JSON.parse(source.textContent); } catch (_error) { return; }

  const escapeHTML = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
  const teamLink = (team) => `<a href="${baseurl}${escapeHTML(team.path)}">${escapeHTML(team.display_name)}</a>`;
  const gameLine = (game) => {
    const a = game.team_a;
    const b = game.team_b;
    const winner = game.tie ? "Tie" : `${escapeHTML(game.winner.display_name)} won`;
    return `<li><span>${game.season} · Week ${game.week}</span><strong>${escapeHTML(a.display_name)} ${a.score} — ${b.score} ${escapeHTML(b.display_name)}</strong><small>${winner}${game.playoff_round ? ` · ${escapeHTML(game.playoff_round)}` : ""}</small></li>`;
  };

  const render = () => {
    const a = selectA.value;
    const b = selectB.value;
    if (!a || !b || a === b) {
      result.innerHTML = `<div class="empty-state"><span class="empty-state__mark" aria-hidden="true">H2H</span><div><h3>${a === b && a ? "Choose two different franchises" : "Select two franchises"}</h3><p>The verified series record will appear here.</p></div></div>`;
      return;
    }
    const pairId = [a, b].sort().join("--");
    const pair = payload.pairs.find((item) => item.pair_id === pairId);
    if (!pair) {
      result.innerHTML = `<div class="empty-state"><span class="empty-state__mark" aria-hidden="true">—</span><div><h3>No verified meetings</h3><p>No resolved 2022–2025 matchup connects these franchises.</p></div></div>`;
      return;
    }
    const selectedAIsCanonicalA = a === pair.franchise_a.franchise_id;
    const first = selectedAIsCanonicalA ? pair.franchise_a : pair.franchise_b;
    const second = selectedAIsCanonicalA ? pair.franchise_b : pair.franchise_a;
    const firstWins = selectedAIsCanonicalA ? pair.wins_a : pair.wins_b;
    const secondWins = selectedAIsCanonicalA ? pair.wins_b : pair.wins_a;
    const firstPoints = selectedAIsCanonicalA ? pair.points_a : pair.points_b;
    const secondPoints = selectedAIsCanonicalA ? pair.points_b : pair.points_a;
    const streak = pair.current_series_streak;
    const streakTeam = streak ? [pair.franchise_a, pair.franchise_b].find((team) => team.franchise_id === streak.franchise_id) : null;
    result.innerHTML = `
      <header class="h2h-score"><div>${teamLink(first)}<strong>${firstWins}</strong></div><span>${pair.ties ? `${pair.ties} tie${pair.ties === 1 ? "" : "s"}` : "series"}</span><div>${teamLink(second)}<strong>${secondWins}</strong></div></header>
      <div class="h2h-metrics">
        <article><span>Meetings</span><strong>${pair.meetings}</strong></article>
        <article><span>Total points</span><strong>${firstPoints}–${secondPoints}</strong></article>
        <article><span>Average margin</span><strong>${pair.average_margin}</strong></article>
        <article><span>Current streak</span><strong>${streak ? `${escapeHTML(streakTeam.display_name)} W${streak.wins}` : "None"}</strong></article>
        <article><span>Playoff meetings</span><strong>${pair.playoff_meetings}</strong></article>
      </div>
      <div class="record-subhead"><div><p class="eyebrow">Latest chapters</p><h3>Recent Meetings</h3></div></div>
      <ol class="h2h-meetings">${pair.recent_meetings.map(gameLine).join("")}</ol>`;
  };
  selectA.addEventListener("change", render);
  selectB.addEventListener("change", render);
})();
