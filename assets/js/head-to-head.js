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
  const pairTeam = (pair, id) => [pair.franchise_a, pair.franchise_b].find((team) => team.franchise_id === id);
  const gameLine = (game) => {
    const a = game.team_a;
    const b = game.team_b;
    const winner = game.tie ? "Tie" : `${escapeHTML(game.winner.display_name)} won by ${game.margin}`;
    return `<li><span>${game.season} · Week ${game.week}</span><strong>${escapeHTML(a.display_name)} ${a.score} — ${b.score} ${escapeHTML(b.display_name)}</strong><small>${winner}${game.playoff_round ? ` · ${escapeHTML(game.playoff_round)}` : ""}</small></li>`;
  };
  const fact = (label, game, value = null) => game
    ? `<article><span>${label}</span><strong>${value ?? `${game.margin} pts`}</strong><small>${game.season} · Week ${game.week}</small></article>`
    : `<article><span>${label}</span><strong>—</strong><small>No decided meeting</small></article>`;

  const updateURL = (a, b) => {
    const url = new URL(window.location.href);
    if (a && b && a !== b) {
      url.searchParams.set("a", a);
      url.searchParams.set("b", b);
    } else {
      url.searchParams.delete("a");
      url.searchParams.delete("b");
    }
    window.history.replaceState({}, "", url);
  };

  const render = () => {
    const a = selectA.value;
    const b = selectB.value;
    updateURL(a, b);
    if (!a || !b || a === b) {
      result.innerHTML = `<div class="empty-state"><span class="empty-state__mark" aria-hidden="true">H2H</span><div><h3>${a === b && a ? "Choose two different franchises" : "Select two franchises"}</h3><p>The complete 2021–2025 series will appear here.</p></div></div>`;
      return;
    }
    const pair = payload.pairs.find((item) => item.pair_id === [a, b].sort().join("--"));
    if (!pair) {
      result.innerHTML = `<div class="empty-state"><span class="empty-state__mark" aria-hidden="true">—</span><div><h3>No verified meetings</h3><p>No resolved 2021–2025 matchup connects these franchises.</p></div></div>`;
      return;
    }
    const selectedAIsCanonicalA = a === pair.franchise_a.franchise_id;
    const first = selectedAIsCanonicalA ? pair.franchise_a : pair.franchise_b;
    const second = selectedAIsCanonicalA ? pair.franchise_b : pair.franchise_a;
    const firstWins = selectedAIsCanonicalA ? pair.wins_a : pair.wins_b;
    const secondWins = selectedAIsCanonicalA ? pair.wins_b : pair.wins_a;
    const firstPoints = selectedAIsCanonicalA ? pair.points_a : pair.points_b;
    const secondPoints = selectedAIsCanonicalA ? pair.points_b : pair.points_a;
    const firstAverage = selectedAIsCanonicalA ? pair.average_score_a : pair.average_score_b;
    const secondAverage = selectedAIsCanonicalA ? pair.average_score_b : pair.average_score_a;
    const firstLargest = selectedAIsCanonicalA ? pair.largest_win_a : pair.largest_win_b;
    const secondLargest = selectedAIsCanonicalA ? pair.largest_win_b : pair.largest_win_a;
    const firstPlayoffWins = selectedAIsCanonicalA ? pair.playoff_wins_a : pair.playoff_wins_b;
    const secondPlayoffWins = selectedAIsCanonicalA ? pair.playoff_wins_b : pair.playoff_wins_a;
    const firstChampionshipWins = selectedAIsCanonicalA ? pair.championship_wins_a : pair.championship_wins_b;
    const secondChampionshipWins = selectedAIsCanonicalA ? pair.championship_wins_b : pair.championship_wins_a;
    const streak = pair.current_series_streak;
    const streakTeam = streak ? pairTeam(pair, streak.franchise_id) : null;
    const longest = pair.longest_series_streak;
    const longestTeam = longest ? pairTeam(pair, longest.franchise_id) : null;
    const playoffGames = pair.all_meetings.filter((game) => game.game_type === "championship_playoff");
    const championshipGames = playoffGames.filter((game) => game.playoff_round === "Championship");
    result.innerHTML = `
      <header class="h2h-score"><div>${teamLink(first)}<strong>${firstWins}</strong></div><span>${pair.ties ? `${pair.ties} tie${pair.ties === 1 ? "" : "s"}` : "series"}</span><div>${teamLink(second)}<strong>${secondWins}</strong></div></header>
      <div class="h2h-metrics">
        <article><span>Meetings</span><strong>${pair.meetings}</strong></article>
        <article><span>Total points</span><strong>${firstPoints}–${secondPoints}</strong></article>
        <article><span>Average score</span><strong>${firstAverage}–${secondAverage}</strong></article>
        <article><span>Average margin</span><strong>${pair.average_margin}</strong></article>
        <article><span>Current streak</span><strong>${streak ? `${escapeHTML(streakTeam.display_name)} W${streak.wins}` : "None"}</strong></article>
        <article><span>Longest series streak</span><strong>${longest ? `${escapeHTML(longestTeam.display_name)} W${longest.wins}` : "None"}</strong></article>
        <article><span>Playoff series</span><strong>${firstPlayoffWins}–${secondPlayoffWins}</strong><small>${pair.playoff_meetings} meetings</small></article>
        <article><span>Championship series</span><strong>${firstChampionshipWins}–${secondChampionshipWins}</strong><small>${pair.championship_meetings} finals</small></article>
      </div>
      <div class="record-subhead"><div><p class="eyebrow">Series landmarks</p><h3>${pair.rivalry_title ? escapeHTML(pair.rivalry_title) : "Rivalry Snapshot"}</h3>${pair.editorial_history ? `<p>${escapeHTML(pair.editorial_history)}</p>` : ""}</div><p class="h2h-range">First: ${pair.first_meeting.season} W${pair.first_meeting.week} · Latest: ${pair.most_recent_meeting.season} W${pair.most_recent_meeting.week}</p></div>
      <div class="h2h-landmarks">
        ${fact(`${escapeHTML(first.display_name)} largest win`, firstLargest)}
        ${fact(`${escapeHTML(second.display_name)} largest win`, secondLargest)}
        ${fact("Closest game", pair.closest_meeting)}
        ${fact("Highest combined score", pair.highest_scoring_meeting, pair.highest_scoring_meeting.combined_score)}
        ${fact("Lowest combined score", pair.lowest_scoring_meeting, pair.lowest_scoring_meeting.combined_score)}
      </div>
      <div class="record-subhead"><div><p class="eyebrow">Latest chapters</p><h3>Recent Meetings</h3></div></div>
      <ol class="h2h-meetings">${pair.recent_meetings.map(gameLine).join("")}</ol>
      <div class="h2h-postseason">
        <section><h3>Playoff Meetings</h3>${playoffGames.length ? `<ol class="h2h-meetings">${playoffGames.map(gameLine).join("")}</ol>` : "<p>No classified championship-bracket meetings.</p>"}</section>
        <section><h3>Championship Meetings</h3>${championshipGames.length ? `<ol class="h2h-meetings">${championshipGames.map(gameLine).join("")}</ol>` : "<p>No championship meetings.</p>"}</section>
      </div>`;
  };

  const valid = new Set([...selectA.options].map((option) => option.value));
  const params = new URLSearchParams(window.location.search);
  if (valid.has(params.get("a"))) selectA.value = params.get("a");
  if (valid.has(params.get("b"))) selectB.value = params.get("b");
  selectA.addEventListener("change", render);
  selectB.addEventListener("change", render);
  render();
})();
