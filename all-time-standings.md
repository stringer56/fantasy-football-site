---
layout: default
title: All-Time Franchise Standings
permalink: /all-time-standings/
description: Canonical Road to Glory franchise standings for the verified 2021–2025 league archive.
---

{% assign career = site.data.generated.records.franchise_career %}

{% include page-hero.html eyebrow="Verified League History — 2021–2025" title="All-Time Franchise Standings" description="Every historical team name rolls into one canonical franchise record. The default order is win percentage, then wins, then points for." compact=true %}

<nav class="records-jump" aria-label="Historical statistics sections"><div class="wrap"><a href="{{ '/all-time-standings/' | relative_url }}" aria-current="page">Standings</a><a href="{{ '/head-to-head/' | relative_url }}">Head-to-Head</a><a href="{{ '/records/' | relative_url }}">Record Book</a><a href="{{ '/championships/' | relative_url }}">Championships</a></div></nav>

<section class="shell-content records-section all-time-standings" aria-labelledby="all-time-heading">
  <div class="section-heading">
    <div><p class="eyebrow">Canonical franchise totals</p><h2 id="all-time-heading">2021–2025 Leaderboard</h2><p>{{ career.ranking_rule }}</p></div>
    <span class="coverage-badge coverage-badge--complete">{{ career.season_level_coverage.label }}</span>
  </div>
  <p class="table-scroll-note">Swipe horizontally to see every category. Select a column heading to reorder the table.</p>
  <div class="record-table-wrap" tabindex="0" role="region" aria-label="All-Time League History 2021 to 2025 franchise standings">
    <table class="record-table record-table--career" data-all-time-table>
      <thead><tr>
        <th data-static>Rank</th>
        <th aria-sort="none"><button type="button" data-sort="name" data-type="text">Franchise</button></th>
        <th aria-sort="none"><button type="button" data-sort="seasons" data-type="number">Seasons</button></th>
        <th aria-sort="none"><button type="button" data-sort="wins" data-type="number">W</button></th>
        <th aria-sort="none"><button type="button" data-sort="losses" data-type="number">L</button></th>
        <th aria-sort="none"><button type="button" data-sort="ties" data-type="number">T</button></th>
        <th aria-sort="descending"><button type="button" data-sort="pct" data-type="number">Win %</button></th>
        <th aria-sort="none"><button type="button" data-sort="pf" data-type="number">PF</button></th>
        <th aria-sort="none"><button type="button" data-sort="pa" data-type="number">PA</button></th>
        <th aria-sort="none"><button type="button" data-sort="playoffs" data-type="number">Playoff Apps</button></th>
        <th aria-sort="none"><button type="button" data-sort="titles" data-type="number">Titles</button></th>
      </tr></thead>
      <tbody>
        {% for row in career.franchises %}
          {% assign season = row.season_history %}
          {% assign playoff = row.playoff_history %}
          <tr data-name="{{ row.display_name | downcase | escape }}" data-seasons="{{ season.season_count }}" data-wins="{{ season.wins }}" data-losses="{{ season.losses }}" data-ties="{{ season.ties }}" data-pct="{{ season.win_percentage }}" data-pf="{{ season.points_for }}" data-pa="{{ season.points_against }}" data-playoffs="{% if playoff %}{{ playoff.playoff_appearances }}{% else %}0{% endif %}" data-titles="{{ season.championships }}">
            <td class="record-rank" data-rank>{{ row.rank }}</td>
            <td><a class="record-team" href="{{ row.path | relative_url }}"><img src="{{ row.identity_image | relative_url }}" alt="" loading="lazy"><span>{{ row.display_name }}</span></a></td>
            <td>{{ season.season_count }}</td><td>{{ season.wins }}</td><td>{{ season.losses }}</td><td>{{ season.ties }}</td>
            <td>{{ season.win_percentage | times: 100 | round: 1 }}%</td><td>{{ season.points_for }}</td><td>{{ season.points_against }}</td>
            <td>{% if playoff %}{{ playoff.playoff_appearances }}{% else %}0{% endif %}</td><td>{{ season.championships }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  <p class="record-source">Season record and PF/PA totals use final standings. Weekly averages and detailed playoff totals on franchise pages use the separately labelled verified matchup archive.</p>
</section>

<script src="{{ '/assets/js/all-time-standings.js' | relative_url }}" defer></script>
