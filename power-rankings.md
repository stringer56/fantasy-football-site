---
layout: default
title: 2026 Manager Power Rankings
permalink: /power-rankings/
description: Current manager-voted Road to Glory FFL Power Rankings and every finalized weekly movement across 2026.
body_class: power-rankings-page
---

{% assign power = site.data.generated.power_rankings %}
{% assign history = site.data.generated.power_rankings_history %}
{% include page-hero.html eyebrow="Twelve ballots. One order." title="2026 Power Rankings" description="Manager ballots only. Yahoo standings, projections, and algorithms never enter the ranking." compact=true %}

<section class="shell-content power-section" aria-labelledby="current-rankings-heading">
  <div class="ranking-method"><div><p class="eyebrow">The ballot</p><h2 id="current-rankings-heading">Current Rankings</h2><p>First earns 12 points, second earns 11, and twelfth earns 1. The latest valid weekly submission from each manager counts once.</p></div><dl><div><dt>Week</dt><dd>{{ power.week | default: '—' }}</dd></div><div><dt>Ballots</dt><dd>{{ power.ballots_counted }}</dd></div><div><dt>Input</dt><dd>Managers</dd></div></dl></div>
  {% if power.rankings.size > 0 %}
    <p class="table-scroll-note">Swipe horizontally to see every ranking field.</p><div class="vote-table-wrap" role="region" aria-label="Current manager-voted Power Rankings" tabindex="0"><table class="vote-table power-table"><thead><tr><th scope="col">Rank</th><th scope="col">Franchise</th><th scope="col">Average manager rank</th><th scope="col">Ranking points</th><th scope="col">First-place votes</th><th scope="col">Previous rank</th><th scope="col">Movement</th></tr></thead><tbody>{% for team in power.rankings %}<tr data-power-ranking-row><td class="vote-rank">{{ team.rank }}</td><td><a class="vote-team" href="{{ team.path | relative_url }}"><img src="{{ team.identity_image | relative_url }}" alt=""><span>{{ team.display_name }}</span></a></td><td>{{ team.average_rank }}</td><td>{{ team.ranking_points | default: team.total_points }}</td><td>{{ team.first_place_votes }}</td><td>{{ team.previous_rank | default: '—' }}</td><td>{% if team.movement == null %}<span class="movement">—</span>{% elsif team.movement > 0 %}<span class="movement movement--up" aria-label="up {{ team.movement }} places">▲ {{ team.movement }}</span>{% elsif team.movement < 0 %}<span class="movement movement--down" aria-label="down {{ team.movement | abs }} places">▼ {{ team.movement | abs }}</span>{% else %}<span class="movement" aria-label="no movement">—</span>{% endif %}</td></tr>{% endfor %}</tbody></table></div>
  {% else %}
    <div class="vote-empty"><span aria-hidden="true">12</span><div><h3>Week 1 ballots have not been finalized.</h3><p>No placeholder order is shown. The table will publish all twelve teams after a commissioner-reviewed import.</p></div></div>
  {% endif %}
</section>

<section class="content-section content-section--neutral power-section" aria-labelledby="ranking-history-heading"><div class="wrap">
  <div class="section-heading"><div><p class="eyebrow eyebrow--dark">Every finalized week</p><h2 id="ranking-history-heading">Power Ranking Movement</h2><p id="ranking-history-summary">Rank 1 is at the top. Filter one or several franchises without hiding the accessible weekly tables below.</p></div></div>
  {% if history.weeks.size > 0 %}
    <div class="power-chart" data-power-chart aria-describedby="ranking-history-summary">
      <div class="power-chart__controls" aria-label="Power Ranking chart filters"><button type="button" data-power-action="all">Show all</button><button type="button" data-power-action="top">Top 3</button><button type="button" data-power-action="clear">Clear</button><label for="power-team-select">Choose a franchise</label><select id="power-team-select" data-power-select><option value="">Select team</option>{% for team in history.franchises %}<option value="{{ team.franchise_id }}">{{ team.display_name }}</option>{% endfor %}</select><button type="button" data-power-action="add">Add team</button></div>
      <div class="power-chart__legend" data-power-legend aria-label="Toggle franchise lines"></div>
      <div class="power-chart__canvas"><svg data-power-svg role="img" aria-labelledby="ranking-history-heading ranking-history-summary"></svg><div class="power-chart__tooltip" data-power-tooltip role="tooltip" hidden></div></div>
      <p class="power-chart__selection" data-power-selection aria-live="polite"></p>
    </div>
    <script type="application/json" id="power-ranking-history-data">{{ history | jsonify }}</script>
  {% else %}
    <div class="vote-empty"><span aria-hidden="true">↗</span><div><h3>The movement chart begins after two finalized weeks.</h3><p>Week 1 will establish the opening positions; later finalized votes add movement without overwriting prior results.</p></div></div>
  {% endif %}
</div></section>

<section class="shell-content power-section" aria-labelledby="power-facts-heading"><div class="section-heading"><div><p class="eyebrow">Voting-derived, not standings</p><h2 id="power-facts-heading">Season Power Ranking Facts</h2></div></div>{% if history.season_facts.size > 0 %}<div class="power-facts-grid">{% for fact in history.season_facts %}<article><span>{{ fact.label }}</span><strong>{{ fact.value }}</strong><p>{% for team in fact.leaders %}<a href="{{ team.path | relative_url }}">{{ team.display_name }}</a>{% unless forloop.last %}, {% endunless %}{% endfor %}</p></article>{% endfor %}</div>{% else %}<div class="live-empty-inline"><strong>Season facts require finalized weekly rankings.</strong><p>Stability, volatility, peaks, rises, and falls are calculated only from the immutable weekly archive.</p></div>{% endif %}</section>

{% if history.weeks.size > 0 %}<section class="content-section content-section--neutral power-section" aria-labelledby="ranking-archive-heading"><div class="wrap"><div class="section-heading"><div><p class="eyebrow eyebrow--dark">Accessible source tables</p><h2 id="ranking-archive-heading">Weekly Ranking Archive</h2></div></div><div class="power-week-archive">{% for week in history.weeks %}<details{% if forloop.first %} open{% endif %}><summary>Week {{ week.week }} · {{ week.ballots_counted }} ballots</summary><div class="vote-table-wrap" role="region" aria-label="Week {{ week.week }} finalized Power Rankings" tabindex="0"><table class="vote-table"><thead><tr><th>Rank</th><th>Franchise</th><th>Average</th><th>Points</th><th>Firsts</th><th>Movement</th></tr></thead><tbody>{% for team in week.rankings %}<tr><td>{{ team.rank }}</td><td><a href="{{ team.path | relative_url }}">{{ team.display_name }}</a></td><td>{{ team.average_rank }}</td><td>{{ team.ranking_points }}</td><td>{{ team.first_place_votes }}</td><td>{% if team.movement > 0 %}▲ {{ team.movement }}{% elsif team.movement < 0 %}▼ {{ team.movement | abs }}{% else %}—{% endif %}</td></tr>{% endfor %}</tbody></table></div></details>{% endfor %}</div></div></section>{% endif %}

<script src="{{ '/assets/js/power-rankings.js' | relative_url }}" defer></script>
