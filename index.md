---
layout: default
title: Home
description: Road to Glory FFL league headquarters—current standings, weekly matchups, draft countdown, and league history.
body_class: home-page
---

{% assign current_season = site.data.site.current_season %}
{% assign generated = site.data.generated %}
{% assign generated_season = generated.manifest.season %}
{% assign data_is_current = false %}
{% if generated.manifest.status == 'ready' and generated_season == current_season %}
  {% assign data_is_current = true %}
{% endif %}
{% assign standings_data = generated.standings %}
{% assign matchups_data = generated.matchups %}
{% capture season_hq_title %}{{ current_season }} League HQ{% endcapture %}

<section class="home-hero">
  <div class="wrap home-hero__inner">
    <div>
      <p class="eyebrow">Road to Glory Fantasy Football League</p>
      <h1>Road to Glory <span>FFL</span></h1>
      <p class="home-hero__lede">A fantasy football league built on rivalries, history, and the pursuit of the Brew Crew Cup.</p>
      <p class="home-hero__meta">{{ current_season }} Season · League Headquarters</p>
      <div class="hero-actions">
        <a class="button button--gold" href="{{ '/teams/' | relative_url }}">View Teams</a>
        <a class="button button--light" href="{{ '/history/' | relative_url }}">League History</a>
        <a class="button button--outline-light" href="{{ site.data.site.yahoo.league_url }}" target="_blank" rel="noopener">Yahoo League <span aria-hidden="true">↗</span></a>
      </div>
    </div>

    <div class="hero-crest" role="img" aria-label="Placeholder for the official Road to Glory league crest or trophy image">
      <div class="hero-crest__center" aria-hidden="true">
        <span class="hero-crest__monogram">RTG</span>
        <span class="hero-crest__label">League HQ</span>
      </div>
      <span class="hero-crest__placeholder" aria-hidden="true">Official crest space</span>
    </div>
  </div>
</section>

<aside class="news-strip" aria-label="League news">
  <div class="wrap news-strip__inner">
    <div class="news-strip__title">League Wire</div>
    <div class="ticker-viewport">
      {% if site.data.news and site.data.news.items and site.data.news.items.size > 0 %}
        <div class="ticker">
          {% for item in site.data.news.items %}
            <span class="ticker__item"><span class="ticker__source">{{ item.source }}</span><a href="{{ item.link }}" target="_blank" rel="noopener">{{ item.title }}</a></span>
          {% endfor %}
          <span aria-hidden="true">
            {% for item in site.data.news.items %}
              <span class="ticker__item"><span class="ticker__source">{{ item.source }}</span><a href="{{ item.link }}" tabindex="-1" rel="noopener">{{ item.title }}</a></span>
            {% endfor %}
          </span>
        </div>
      {% else %}
        <div class="news-empty">League news is being updated.</div>
      {% endif %}
    </div>
  </div>
</aside>

<section class="content-section content-section--neutral" aria-labelledby="season-hq-heading">
  <div class="wrap">
    {% include section-heading.html id="season-hq-heading" eyebrow="Current season" title=season_hq_title description="Draft-day readiness and the live league pulse, built to stay useful before, during, and after the season." %}
    <div class="season-grid">
      <article class="draft-panel">
        <p class="eyebrow">On the clock</p>
        <h3>Draft Day Countdown</h3>
        <p class="draft-panel__description">The road to the Brew Crew Cup begins at the draft table.</p>
        {% assign draft_datetime = site.data.league.draft_datetime %}
        <div id="draft-countdown" class="countdown{% unless draft_datetime %} is-tba{% endunless %}" data-datetime="{% if draft_datetime %}{{ draft_datetime | date_to_xmlschema }}{% endif %}" data-season="{{ current_season }}" data-complete-message="The {{ current_season }} draft is complete.">
          <div class="countdown-grid" aria-hidden="true">
            <div class="countdown-unit"><span class="countdown-unit__value" data-countdown-days>--</span><span class="countdown-unit__label">Days</span></div>
            <div class="countdown-unit"><span class="countdown-unit__value" data-countdown-hours>--</span><span class="countdown-unit__label">Hours</span></div>
            <div class="countdown-unit"><span class="countdown-unit__value" data-countdown-minutes>--</span><span class="countdown-unit__label">Minutes</span></div>
            <div class="countdown-unit"><span class="countdown-unit__value" data-countdown-seconds>--</span><span class="countdown-unit__label">Seconds</span></div>
          </div>
          <p class="countdown-status" data-countdown-status>{% if draft_datetime %}Draft countdown loading. Draft date: <time datetime="{{ draft_datetime | date_to_xmlschema }}">{{ draft_datetime | date: '%B %-d, %Y at %-I:%M %p %Z' }}</time>.{% else %}{{ current_season }} Draft Date TBA{% endif %}</p>
        </div>
      </article>

      <aside class="league-brief">
        <div>
          <span class="league-brief__season" aria-hidden="true">{{ current_season }}</span>
          <h3>Season Status</h3>
          {% if data_is_current %}
            <p>Yahoo league data is current for {{ current_season }} and ready across the league dashboard.</p>
          {% else %}
            <p>The {{ current_season }} league is configured. Live standings and matchups will appear when Yahoo publishes the new season data.</p>
          {% endif %}
        </div>
        <a class="text-link" href="{{ site.data.site.yahoo.league_url }}" target="_blank" rel="noopener">Open Yahoo League <span aria-hidden="true">↗</span></a>
      </aside>
    </div>
  </div>
</section>

<section class="content-section" aria-labelledby="standings-heading">
  <div class="wrap">
    {% include section-heading.html id="standings-heading" eyebrow="League table" title="Current Standings" description="Wins, losses, and the scoring race from the normalized Yahoo league feed." %}
    <div class="panel">
      <div class="panel__header">
        <h3>{{ current_season }} Standings</h3>
        {% if data_is_current and standings_data.standings %}<span class="panel__meta">{{ standings_data.standings.size }} teams</span>{% else %}<span class="panel__meta">Preseason</span>{% endif %}
      </div>
      {% if data_is_current and standings_data and standings_data.standings and standings_data.standings.size > 0 %}
        <div class="table-scroll" role="region" aria-label="Current league standings; scroll horizontally for all statistics" tabindex="0">
          <table class="standings-table">
            <thead><tr><th scope="col">Rank</th><th scope="col">Team</th><th scope="col">W</th><th scope="col">L</th><th scope="col">T</th><th scope="col">Win %</th><th scope="col">PF</th><th scope="col">PA</th></tr></thead>
            <tbody>
              {% for team in standings_data.standings %}
                <tr{% if team.rank and team.rank <= 3 %} class="rank-highlight"{% endif %}>
                  <td class="rank-cell">{{ team.rank | default: forloop.index }}</td>
                  <td class="standings-team">{{ team.team_name }}</td>
                  <td class="standings-record">{{ team.wins }}</td><td class="standings-record">{{ team.losses }}</td><td class="standings-record">{{ team.ties }}</td>
                  <td>{{ team.winning_percentage | times: 100.0 | round: 1 }}%</td><td class="standings-points">{{ team.points_for | round: 2 }}</td><td class="standings-points">{{ team.points_against | round: 2 }}</td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      {% else %}
        {% include empty-state.html title="Standings arrive with the season" description="League data is being updated. The full table will appear here when the 2026 Yahoo season publishes standings." href="/history/" link_text="Explore league history" %}
      {% endif %}
    </div>
  </div>
</section>

<section class="content-section content-section--navy" aria-labelledby="matchups-heading">
  <div class="wrap">
    {% include section-heading.html id="matchups-heading" eyebrow="Head to head" title="Weekly Matchups" description="Scoreboard-style matchup cards with projections, final results, and rosters available on demand." %}
    {% if data_is_current and matchups_data and matchups_data.matchups and matchups_data.matchups.size > 0 %}
      <div class="matchup-grid">
        {% for matchup in matchups_data.matchups %}
          {% assign team_a = matchup.teams[0] %}
          {% assign team_b = matchup.teams[1] %}
          {% capture matchup_status %}{% case matchup.status %}{% when 'postevent' %}Final{% when 'midevent' %}In Progress{% when 'preevent' %}Upcoming{% else %}{{ matchup.status | default: 'Scheduled' | replace: '_', ' ' | capitalize }}{% endcase %}{% endcapture %}
          <article class="matchup-card">
            <header class="matchup-card__header"><span>Week {{ matchup.week | default: matchups_data.week }}</span><span class="matchup-card__type">{% if matchup.is_consolation %}Consolation{% elsif matchup.is_playoffs %}Playoffs{% else %}Regular Season{% endif %} · {{ matchup_status | strip }}</span></header>
            <div class="matchup-team{% if matchup.winner_team_key == team_a.team_key %} is-winner{% endif %}">
              <div class="matchup-team__name"><span class="matchup-team__seed" aria-hidden="true">A</span><span>{{ team_a.team_name }}</span></div>
              <div class="matchup-team__score-wrap"><span class="matchup-team__score">{{ team_a.score | default: '—' }}</span>{% if team_a.projected_score %}<span class="matchup-team__projection">Proj. {{ team_a.projected_score }}</span>{% endif %}</div>
            </div>
            <div class="matchup-team{% if matchup.winner_team_key == team_b.team_key %} is-winner{% endif %}">
              <div class="matchup-team__name"><span class="matchup-team__seed" aria-hidden="true">B</span><span>{{ team_b.team_name }}</span></div>
              <div class="matchup-team__score-wrap"><span class="matchup-team__score">{{ team_b.score | default: '—' }}</span>{% if team_b.projected_score %}<span class="matchup-team__projection">Proj. {{ team_b.projected_score }}</span>{% endif %}</div>
            </div>
            <div class="matchup-card__rosters">{% include roster.html team=team_a %}{% include roster.html team=team_b %}</div>
          </article>
        {% endfor %}
      </div>
    {% else %}
      {% include empty-state.html title="The next slate is taking shape" description="League data is being updated. Matchup cards and collapsed team rosters will appear here when the 2026 schedule is available." href="/teams/" link_text="Meet the franchises" %}
    {% endif %}
  </div>
</section>

<section class="content-section content-section--neutral">
  <div class="wrap">
    <div class="cup-feature">
      <div class="cup-feature__mark" aria-hidden="true">BC</div>
      <div><p class="eyebrow">League immortality</p><h2>The Brew Crew <span>Cup</span></h2><p>Every draft, rivalry, and playoff run leads to one prize. Explore the history of the Brew Crew Cup and the championship stories that define Road to Glory.</p><a class="button button--gold" href="{{ '/cup/' | relative_url }}">Explore Cup History</a></div>
    </div>
  </div>
</section>

<section class="content-section" aria-labelledby="explore-heading">
  <div class="wrap">
    {% include section-heading.html id="explore-heading" eyebrow="Around the league" title="Explore Road to Glory" description="The league archive is being built as a connected home for franchises, seasons, drafts, records, and community traditions." %}
    <div class="explore-grid">
      <a class="explore-card" href="{{ '/teams/' | relative_url }}"><span class="explore-card__number">01</span><div><h3>Teams &amp; Owners</h3><p>Franchise identities, ownership, rivalries, and season-by-season continuity.</p><span class="explore-card__arrow" aria-hidden="true">→</span></div></a>
      <a class="explore-card" href="{{ '/history/' | relative_url }}"><span class="explore-card__number">02</span><div><h3>League History</h3><p>Season standings, playoff brackets, championship games, and recap stories.</p><span class="explore-card__arrow" aria-hidden="true">→</span></div></a>
      <a class="explore-card" href="{{ '/drafts/' | relative_url }}"><span class="explore-card__number">03</span><div><h3>Draft Archive</h3><p>Draft orders, results, and the choices that changed each season.</p><span class="explore-card__arrow" aria-hidden="true">→</span></div></a>
      <a class="explore-card" href="{{ '/cup/' | relative_url }}"><span class="explore-card__number">04</span><div><h3>Brew Crew Cup</h3><p>The league trophy, championship runs, and the pursuit of league immortality.</p><span class="explore-card__arrow" aria-hidden="true">→</span></div></a>
      <a class="explore-card" href="{{ '/records/' | relative_url }}"><span class="explore-card__number">05</span><div><h3>Records &amp; Leaders</h3><p>Career marks, scoring performances, streaks, margins, and milestones.</p><span class="explore-card__arrow" aria-hidden="true">→</span></div></a>
      <a class="explore-card" href="{{ '/votes/' | relative_url }}"><span class="explore-card__number">06</span><div><h3>League Votes</h3><p>Power rankings, weekly picks, polls, and the voice of the league.</p><span class="explore-card__arrow" aria-hidden="true">→</span></div></a>
    </div>
  </div>
</section>
