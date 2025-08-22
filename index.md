---
layout: default
title: Home
---

<section class="hero">
  <h1>Road to Glory FFL</h1>
  <p>League hub with history, drafts, franchise pages, and live updates.</p>
  <p><span class="badge">Draft Countdown</span> <span id="draft-countdown" class="countdown" data-datetime="{{ site.data.league.draft_datetime }}"></span></p>
</section>

<div class="grid">
  <div class="card">
    <h2>Standings (raw feed)</h2>
    <p>Once the Action runs, standings JSON appears below. We’ll switch to a pretty table next.</p>
    {% if site.data.standings %}<pre>{{ site.data.standings | jsonify }}</pre>{% else %}<p><em>Waiting for _data/standings.json…</em></p>{% endif %}
  </div>

  <div class="card">
    <h2>This Week's Scoreboard (raw feed)</h2>
    {% if site.data.scoreboard %}<pre>{{ site.data.scoreboard | jsonify }}</pre>{% else %}<p><em>Waiting for _data/scoreboard.json…</em></p>{% endif %}
  </div>

  <div class="card">
    <h2>League Meta</h2>
    {% if site.data.league_meta %}<pre>{{ site.data.league_meta | jsonify }}</pre>{% else %}<p><em>Waiting for _data/league_meta.json…</em></p>{% endif %}
  </div>
</div>
