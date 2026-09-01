---
layout: default
title: Records & Leaderboards
permalink: /records/
description: Verified Road to Glory franchise, season, championship, and playoff records.
---

{% assign record_book = site.data.generated.records %}

<section class="records-hero">
  <div class="wrap records-hero__grid">
    <div>
      <p class="eyebrow">By the numbers</p>
      <h1>Road to Glory<br>Record Book</h1>
      <p class="records-hero__dek">A reproducible league record built from final standings, championship results, and verified playoff brackets—not memory or guesswork.</p>
      <div class="records-hero__actions">
        <a class="button button--gold" href="#career-leaderboards">View the leaders</a>
        <a class="text-link" href="{{ '/history/' | relative_url }}">Open season archive <span aria-hidden="true">→</span></a>
      </div>
    </div>
    <aside class="coverage-scorecard" aria-label="Record book coverage">
      <span class="coverage-scorecard__label">Current coverage</span>
      <strong>2021<span>–</span>2024</strong>
      <p>{{ record_book.coverage.label }}. Five unresolved standings identities are excluded from franchise totals.</p>
      <dl>
        <div><dt>Seasons</dt><dd>{{ record_book.coverage.source_years.size }}</dd></div>
        <div><dt>Published groups</dt><dd>{{ record_book.leaderboards.size | plus: record_book.records.size }}</dd></div>
        <div><dt>Unsupported stats</dt><dd>0</dd></div>
      </dl>
    </aside>
  </div>
</section>

<nav class="records-jump" aria-label="Record book sections"><div class="wrap"><a href="#career-leaderboards">Career</a><a href="#season-records">Season</a><a href="#playoff-records">Playoffs</a><a href="#awaiting-data">In progress</a></div></nav>

<section class="shell-content records-section" id="career-leaderboards" aria-labelledby="career-heading">
  {% assign career = record_book.leaderboards.career_totals %}
  <div class="section-heading">
    <div><p class="eyebrow">Verified franchise totals</p><h2 id="career-heading">Career Leaderboard</h2><p>Resolved franchise results inside the current four-season archive. Rows with an uncertain historical identity are held out.</p></div>
    <span class="coverage-badge coverage-badge--partial">Partial coverage</span>
  </div>
  <p class="table-scroll-note">Swipe horizontally to see the full leaderboard.</p>
  <div class="record-table-wrap" tabindex="0" role="region" aria-label="Franchise career leaderboard">
    <table class="record-table"><thead><tr><th>Rank</th><th>Franchise</th><th>Seasons</th><th>Record</th><th>Win %</th><th>PF</th><th>PA</th><th>Titles</th></tr></thead><tbody>
      {% for entry in career.entries limit: 10 %}<tr><td class="record-rank">{{ entry.rank }}</td><td><a class="record-team" href="{{ entry.path | relative_url }}"><img src="{{ entry.identity_image | relative_url }}" alt="" loading="lazy"><span>{{ entry.display_name }}</span></a></td><td>{{ entry.seasons_counted }}</td><td>{{ entry.wins }}–{{ entry.losses }}{% if entry.ties > 0 %}–{{ entry.ties }}{% endif %}</td><td>{{ entry.win_pct | times: 100 | round: 1 }}%</td><td>{{ entry.points_for }}</td><td>{{ entry.points_against }}</td><td>{{ entry.championships }}</td></tr>{% endfor %}
    </tbody></table>
  </div>
  {% if career.entries.size > 10 %}
    <details class="record-more"><summary>Show remaining verified franchises</summary><div class="record-table-wrap" tabindex="0" role="region" aria-label="Remaining franchise career totals"><table class="record-table"><thead><tr><th>Rank</th><th>Franchise</th><th>Seasons</th><th>Record</th><th>Win %</th><th>PF</th><th>PA</th><th>Titles</th></tr></thead><tbody>
      {% for entry in career.entries offset: 10 %}<tr><td class="record-rank">{{ entry.rank }}</td><td><a class="record-team" href="{{ entry.path | relative_url }}"><img src="{{ entry.identity_image | relative_url }}" alt="" loading="lazy"><span>{{ entry.display_name }}</span></a></td><td>{{ entry.seasons_counted }}</td><td>{{ entry.wins }}–{{ entry.losses }}{% if entry.ties > 0 %}–{{ entry.ties }}{% endif %}</td><td>{{ entry.win_pct | times: 100 | round: 1 }}%</td><td>{{ entry.points_for }}</td><td>{{ entry.points_against }}</td><td>{{ entry.championships }}</td></tr>{% endfor %}
    </tbody></table></div></details>
  {% endif %}
  <p class="record-source">{{ career.provenance.source_years.first }}–{{ career.provenance.source_years.last }} final standings · {{ career.provenance.coverage_status | capitalize }} coverage</p>
</section>

<section class="content-section content-section--navy records-section" id="season-records" aria-labelledby="season-records-heading"><div class="wrap">
  <div class="section-heading section-heading--light"><div><p class="eyebrow">One season. One mark.</p><h2 id="season-records-heading">Season Records</h2><p>Best and lowest verified marks across every final standings row, including unresolved historical names when the season value itself is clear.</p></div><span class="coverage-badge coverage-badge--complete">Results complete</span></div>
  <div class="record-card-grid">
    {% for record in record_book.records.season_results.entries %}<article class="record-card"><p>{{ record.label }}</p><strong>{% if record.format == 'percentage' %}{{ record.holders[0].value | times: 100 | round: 1 }}%{% else %}{{ record.holders[0].value }}{% endif %}</strong><div>{% for holder in record.holders %}<span>{% if holder.path %}<a href="{{ holder.path | relative_url }}">{{ holder.historical_team_name }}</a>{% else %}{{ holder.historical_team_name }}{% endif %} · <a href="{{ holder.season_path | relative_url }}">{{ holder.year }}</a></span>{% endfor %}</div></article>{% endfor %}
    {% for record in record_book.records.season_points.entries %}<article class="record-card"><p>{{ record.label }}</p><strong>{{ record.holders[0].value }}</strong><div>{% for holder in record.holders %}<span>{% if holder.path %}<a href="{{ holder.path | relative_url }}">{{ holder.historical_team_name }}</a>{% else %}{{ holder.historical_team_name }}{% endif %} · <a href="{{ holder.season_path | relative_url }}">{{ holder.year }}</a></span>{% endfor %}</div></article>{% endfor %}
  </div>
  <p class="record-source record-source--dark">Results: complete for 2021–2024 · Scoring: partial while the 2024 PF/PA source conflict remains under review</p>
</div></section>

<section class="shell-content records-section" id="playoff-records" aria-labelledby="playoff-heading">
  <div class="section-heading"><div><p class="eyebrow">The championship road</p><h2 id="playoff-heading">Playoff Records</h2><p>Titles and finals are complete for the verified archive. Playoff totals exclude one unresolved 2021 participant and never treat missing scores as zero.</p></div><a class="button button--outline" href="{{ '/cup/' | relative_url }}">Brew Crew Cup</a></div>
  <div class="honor-board-grid">
    {% assign titles = record_book.leaderboards.championships %}<article class="honor-board"><p class="eyebrow">Championships</p><h3>Title Holders</h3>{% for entry in titles.entries %}<div><span class="honor-board__rank">{{ entry.rank }}</span><a href="{{ entry.path | relative_url }}">{{ entry.display_name }}</a><strong>{{ entry.championships }}</strong></div>{% endfor %}<small>Complete · Verified 2021–2024</small></article>
    {% assign finals = record_book.leaderboards.finals_appearances %}<article class="honor-board"><p class="eyebrow">Championship appearances</p><h3>Finals Leaders</h3>{% for entry in finals.entries %}<div><span class="honor-board__rank">{{ entry.rank }}</span><a href="{{ entry.path | relative_url }}">{{ entry.display_name }}</a><strong>{{ entry.finals_appearances }}</strong></div>{% endfor %}<small>Complete · Verified 2021–2024</small></article>
  </div>
  {% assign playoff_totals = record_book.leaderboards.playoff_results %}
  <div class="record-subhead"><div><p class="eyebrow">Verified bracket results</p><h3>Postseason Totals</h3></div><span class="coverage-badge coverage-badge--partial">Partial coverage</span></div>
  <p class="table-scroll-note">Swipe horizontally to see the full leaderboard.</p>
  <div class="record-table-wrap" tabindex="0" role="region" aria-label="Postseason franchise leaderboard"><table class="record-table record-table--compact"><thead><tr><th>Rank</th><th>Franchise</th><th>Appearances</th><th>Wins</th><th>Losses</th><th>Seasons</th></tr></thead><tbody>
    {% for entry in playoff_totals.entries %}<tr><td class="record-rank">{{ entry.rank }}</td><td><a class="record-team" href="{{ entry.path | relative_url }}"><img src="{{ entry.identity_image | relative_url }}" alt="" loading="lazy"><span>{{ entry.display_name }}</span></a></td><td>{{ entry.appearances }}</td><td>{{ entry.wins }}</td><td>{{ entry.losses }}</td><td>{{ entry.seasons | join: ', ' }}</td></tr>{% endfor %}
  </tbody></table></div>
  {% assign streaks = record_book.leaderboards.playoff_appearance_streaks %}
  <div class="record-subhead"><div><p class="eyebrow">Inside the verified window</p><h3>Consecutive Playoff Appearances</h3></div></div>
  <div class="streak-grid">{% for entry in streaks.entries limit: 5 %}<article><span>#{{ entry.rank }}</span><div><a href="{{ entry.path | relative_url }}">{{ entry.display_name }}</a><small>{{ entry.start_year }}–{{ entry.end_year }}</small></div><strong>{{ entry.streak }}</strong></article>{% endfor %}</div>
</section>

<section class="content-section records-section records-awaiting" id="awaiting-data" aria-labelledby="awaiting-heading"><div class="wrap">
  <div class="section-heading"><div><p class="eyebrow">Next layers of the archive</p><h2 id="awaiting-heading">Still Being Built</h2><p>These categories stay intentionally empty until the complete source history exists.</p></div></div>
  <div class="unavailable-grid">
    {% for category in record_book.unavailable_categories %}{% unless category.category_id == 'bench_blunders' %}<article class="unavailable-card"><span aria-hidden="true">—</span><div><h3>{{ category.label }}</h3><p>{{ category.message }}</p></div></article>{% endunless %}{% endfor %}
    <article class="unavailable-card unavailable-card--bench"><span aria-hidden="true">10</span><div><h3>Bench Blunders</h3><p>Historical bench scoring is still being imported. The Top 10 schema is ready, but no unverified entry will be published.</p></div></article>
  </div>
  <p class="record-method">Every published table carries its source years, source files, coverage state, and generation date in the canonical data. See the <a href="{{ '/history/' | relative_url }}">season archive</a> for the original standings and brackets.</p>
</div></section>
