---
layout: default
title: Home
---

{% assign league = site.data.league_meta.fantasy_content.league | first %}
{% assign sb = site.data.scoreboard_simple %}
{% assign ro = site.data.rosters_simple %}

<section class="hero">
  <div class="shell hero-grid">
    <div>
      <p class="eyebrow">Est. league archive • live Yahoo data</p>
      <h1>Road to Glory</h1>
      <p class="hero-copy">The official home of the Road to Glory Fantasy Football League — current matchups, standings, franchise history, drafts, records and the Brew Crew Cup.</p>
      <div class="hero-actions">
        <a class="button button-primary" href="https://football.fantasysports.yahoo.com/f1/26455" target="_blank" rel="noopener">Open Yahoo League</a>
        <a class="button button-secondary" href="{{ '/seasons/' | relative_url }}">Explore League History</a>
      </div>
    </div>

    <aside class="hero-card">
      {% if league.logo_url %}<img src="{{ league.logo_url }}" alt="Road to Glory FFL logo">{% endif %}
      <small>Current league</small>
      <strong>{{ league.name | default: 'Road To Glory FFL' }}</strong>
      <small>{% if league.season %}{{ league.season }} season • {% endif %}{{ league.num_teams | default: 12 }} franchises</small>
      {% if site.data.league.draft_datetime %}
      <div style="margin-top:16px;">
        <small>Draft countdown</small>
        <strong id="draft-countdown" class="countdown" data-datetime="{{ site.data.league.draft_datetime }}" style="font-size:18px;margin-top:3px;">Loading…</strong>
      </div>
      {% endif %}
    </aside>
  </div>
</section>

{% if site.data.news and site.data.news.items and site.data.news.items.size > 0 %}
<div class="news-bar">
  <div class="shell news-inner">
    <div class="news-label">NFL News</div>
    <div class="ticker-wrap">
      <div class="ticker">
        {% for item in site.data.news.items %}<span><span class="src">{{ item.source }}</span><a href="{{ item.link }}" target="_blank" rel="noopener">{{ item.title }}</a></span>{% endfor %}
        {% for item in site.data.news.items %}<span><span class="src">{{ item.source }}</span><a href="{{ item.link }}" target="_blank" rel="noopener">{{ item.title }}</a></span>{% endfor %}
      </div>
    </div>
  </div>
</div>
{% endif %}

<div class="shell">
  <section class="stat-grid" aria-label="League snapshot">
    <div class="stat-card"><span class="stat-label">Season</span><span class="stat-value">{{ league.season | default: '2026' }}</span></div>
    <div class="stat-card"><span class="stat-label">Franchises</span><span class="stat-value">{{ league.num_teams | default: 12 }}</span></div>
    <div class="stat-card"><span class="stat-label">Current Week</span><span class="stat-value">{{ league.current_week | default: 'Preseason' }}</span></div>
    <div class="stat-card"><span class="stat-label">Scoring</span><span class="stat-value">Head-to-Head</span></div>
  </section>
</div>

<section class="page-section">
  <div class="shell">
    <div class="section-heading">
      <div><h2>League Central</h2><p>The current season at a glance.</p></div>
      <a class="section-link" href="https://football.fantasysports.yahoo.com/f1/26455" target="_blank" rel="noopener">Full league on Yahoo ↗</a>
    </div>

    <div class="content-grid">
      <section class="card">
        <div class="card-header"><h2>Standings</h2><span class="stat-label">Live from Yahoo</span></div>
        <div class="table-wrap">
          {% if site.data.standings_simple and site.data.standings_simple.size > 0 %}
          <table class="table">
            <thead><tr><th>#</th><th>Team</th><th>W</th><th>L</th><th>T</th><th>PF</th><th>PA</th></tr></thead>
            <tbody>
            {% for t in site.data.standings_simple %}
              <tr><td class="rank">{{ forloop.index }}</td><td>{{ t.team }}</td><td>{{ t.wins }}</td><td>{{ t.losses }}</td><td>{{ t.ties }}</td><td>{{ t.points_for }}</td><td>{{ t.points_against }}</td></tr>
            {% endfor %}
            </tbody>
          </table>
          {% else %}
          <div class="card-body empty">Standings will populate after the Yahoo data refresh.</div>
          {% endif %}
        </div>
      </section>

      <section class="card">
        <div class="card-header"><h2>This Week</h2><span class="stat-label">{% if sb.week %}Week {{ sb.week }}{% else %}Matchups{% endif %}</span></div>
        <div class="card-body">
          {% if sb and sb.matchups and sb.matchups.size > 0 %}
          <div class="matchup-list">
            {% for m in sb.matchups %}
            <article class="matchup">
              <div class="matchup-main">
                <div class="matchup-team"><strong>{{ m.team_a }}</strong><span class="matchup-score">{{ m.points_a | default: '—' }}</span></div>
                <span class="matchup-vs">vs</span>
                <div class="matchup-team"><strong>{{ m.team_b }}</strong><span class="matchup-score">{{ m.points_b | default: '—' }}</span></div>
              </div>

              {% if ro and ro.teams %}
                {% assign rosterA = ro.teams | where: 'team', m.team_a | first %}
                {% assign rosterB = ro.teams | where: 'team', m.team_b | first %}
                {% if rosterA or rosterB %}
                <details>
                  <summary>View matchup rosters</summary>
                  {% if rosterA %}<strong style="padding-left:15px;font-size:12px;">{{ m.team_a }}</strong><ul class="roster">{% for p in rosterA.players %}<li>{{ p.position | default: '—' }} — {{ p.name }}</li>{% endfor %}</ul>{% endif %}
                  {% if rosterB %}<strong style="padding-left:15px;font-size:12px;">{{ m.team_b }}</strong><ul class="roster">{% for p in rosterB.players %}<li>{{ p.position | default: '—' }} — {{ p.name }}</li>{% endfor %}</ul>{% endif %}
                </details>
                {% endif %}
              {% endif %}
            </article>
            {% endfor %}
          </div>
          {% else %}
          <p class="empty">Matchups will appear here when Yahoo publishes the current-week scoreboard.</p>
          {% endif %}
        </div>
      </section>
    </div>
  </div>
</section>

<section class="page-section">
  <div class="shell">
    <div class="section-heading"><div><h2>Explore the League</h2><p>The parts of Road to Glory that make the league more than a scoreboard.</p></div></div>
    <div class="link-grid">
      <a class="link-card" href="{{ '/teams/' | relative_url }}"><span>Franchises</span><strong>Teams & Owners</strong><p>Helmets, owners, team write-ups and franchise histories.</p></a>
      <a class="link-card" href="{{ '/seasons/' | relative_url }}"><span>Archive</span><strong>League History</strong><p>Season standings, recaps, playoff brackets and championship stories.</p></a>
      <a class="link-card" href="{{ '/cup/' | relative_url }}"><span>Championship</span><strong>Brew Crew Cup</strong><p>Past champions, trophy history and every road to the title.</p></a>
      <a class="link-card" href="{{ '/drafts/' | relative_url }}"><span>Draft</span><strong>Draft Archive</strong><p>Draft orders, results and year-by-year recaps.</p></a>
      <a class="link-card" href="{{ '/records/' | relative_url }}"><span>Record Book</span><strong>Records & Leaders</strong><p>All-time leaders, scoring records, margins and bench blunders.</p></a>
      <a class="link-card" href="{{ '/votes/' | relative_url }}"><span>League Office</span><strong>Votes & Power Rankings</strong><p>Rule votes, weekly power rankings and matchup predictions.</p></a>
      <a class="link-card" href="{{ '/retired/' | relative_url }}"><span>History</span><strong>Retired Franchises</strong><p>Preserving the teams and owners that are no longer active.</p></a>
      <a class="link-card" href="{{ '/rules/' | relative_url }}"><span>Rulebook</span><strong>League Rules</strong><p>The official rules, scoring and governance of Road to Glory.</p></a>
    </div>
  </div>
</section>
