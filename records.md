---
layout: default
title: Records & Leaderboards
permalink: /records/
description: Verified Road to Glory franchise, season, championship, and playoff records.
---

{% assign record_book = site.data.generated.record_book %}
{% assign historical = site.data.generated.records %}

<section class="records-hero">
  <div class="wrap records-hero__grid">
    <div>
      <p class="eyebrow">By the numbers</p>
      <h1>Road to Glory<br>Record Book</h1>
      <p class="records-hero__dek">A reproducible league record built from final standings, championship results, and verified playoff brackets—not memory or guesswork.</p>
      <div class="records-hero__actions">
        <a class="button button--gold" href="#career-leaderboards">View the leaders</a>
        <a class="text-link" href="{{ '/head-to-head/' | relative_url }}">Compare franchises <span aria-hidden="true">→</span></a>
      </div>
    </div>
    <aside class="coverage-scorecard" aria-label="Record book coverage">
      <span class="coverage-scorecard__label">Current coverage</span>
      <strong>2021<span>–</span>2025</strong>
      <p>Season totals cover 2021–2025. Weekly matchup records use the complete 2022–2025 Yahoo archive.</p>
      <dl>
        <div><dt>Season years</dt><dd>5</dd></div>
        <div><dt>Weekly games</dt><dd>{{ historical.manifest.counts.resolved_matchups }}</dd></div>
        <div><dt>Unsupported stats</dt><dd>0</dd></div>
      </dl>
    </aside>
  </div>
</section>

<nav class="records-jump" aria-label="Record book sections"><div class="wrap"><a href="#career-leaderboards">Career</a><a href="#season-records">Season</a><a href="#weekly-records">Weekly</a><a href="#streak-records">Streaks</a><a href="#playoff-records">Playoffs</a><a href="#awaiting-data">In progress</a></div></nav>

<section class="content-section content-section--navy records-section" id="weekly-records" aria-labelledby="weekly-records-heading"><div class="wrap">
  <div class="section-heading section-heading--light"><div><p class="eyebrow">Final Yahoo matchups</p><h2 id="weekly-records-heading">Weekly Records</h2><p>Every entry below comes from a final, scored matchup with resolved franchise identities.</p></div><span class="coverage-badge coverage-badge--complete">{{ historical.biggest_wins.coverage.label }}</span></div>
  <div class="record-subhead record-subhead--light"><div><p class="eyebrow">Separation at the whistle</p><h3>Biggest Wins</h3></div></div>
  <p class="table-scroll-note">Swipe horizontally to see the full leaderboard.</p>
  <div class="record-table-wrap" tabindex="0" role="region" aria-label="Biggest verified wins"><table class="record-table record-table--weekly"><thead><tr><th>Rank</th><th>Winner</th><th>Opponent</th><th>Score</th><th>Margin</th><th>Game</th></tr></thead><tbody>
    {% for game in historical.biggest_wins.overall %}<tr><td class="record-rank">{{ game.rank }}</td><td><a href="{{ game.winner.path | relative_url }}">{{ game.winner.display_name }}</a></td><td><a href="{{ game.loser.path | relative_url }}">{{ game.loser.display_name }}</a></td><td>{{ game.winner_score }}–{{ game.loser_score }}</td><td>{{ game.margin }}</td><td>{% if game.season == 2025 %}{{ game.season }} W{{ game.week }}{% else %}<a href="{{ '/history/' | append: game.season | append: '/' | relative_url }}">{{ game.season }} W{{ game.week }}</a>{% endif %}</td></tr>{% endfor %}
  </tbody></table></div>
  <div class="record-subhead record-subhead--light"><div><p class="eyebrow">Down to the wire</p><h3>Closest Games</h3></div></div>
  <div class="record-table-wrap" tabindex="0" role="region" aria-label="Closest verified games"><table class="record-table record-table--weekly"><thead><tr><th>Rank</th><th>Winner</th><th>Opponent</th><th>Score</th><th>Margin</th><th>Game</th></tr></thead><tbody>
    {% for game in historical.closest_games.overall %}<tr><td class="record-rank">{{ game.rank }}</td><td><a href="{{ game.winner.path | relative_url }}">{{ game.winner.display_name }}</a></td><td><a href="{{ game.loser.path | relative_url }}">{{ game.loser.display_name }}</a></td><td>{{ game.winner_score }}–{{ game.loser_score }}</td><td>{{ game.margin }}</td><td>{% if game.season == 2025 %}{{ game.season }} W{{ game.week }}{% else %}<a href="{{ '/history/' | append: game.season | append: '/' | relative_url }}">{{ game.season }} W{{ game.week }}</a>{% endif %}</td></tr>{% endfor %}
  </tbody></table></div>
  <div class="record-subhead record-subhead--light"><div><p class="eyebrow">Scoreboard peaks</p><h3>Weekly Scoring</h3></div></div>
  <div class="weekly-record-grid">
    <article><h4>Highest Scores</h4><ol>{% for row in historical.weekly_scores.highest_team_scores %}<li><span>{{ row.rank }}</span><a href="{{ row.path | relative_url }}">{{ row.display_name }}</a><strong>{{ row.score }}</strong><small>{{ row.season }} W{{ row.week }}</small></li>{% endfor %}</ol></article>
    <article><h4>Lowest Scores</h4><ol>{% for row in historical.weekly_scores.lowest_team_scores %}<li><span>{{ row.rank }}</span><a href="{{ row.path | relative_url }}">{{ row.display_name }}</a><strong>{{ row.score }}</strong><small>{{ row.season }} W{{ row.week }}</small></li>{% endfor %}</ol></article>
  </div>
  <p class="record-source record-source--dark">{{ historical.weekly_scores.coverage.label }} · Ties are preserved separately and excluded from closest-win rankings</p>
</div></section>

<section class="shell-content records-section" id="streak-records" aria-labelledby="streak-heading">
  <div class="section-heading"><div><p class="eyebrow">Regular-season runs</p><h2 id="streak-heading">Winning &amp; Losing Streaks</h2><p>Single-season streaks use regular-season results only. Ties break win/loss streaks.</p></div><span class="coverage-badge coverage-badge--partial">{{ historical.streaks.coverage.label }}</span></div>
  <div class="weekly-record-grid">
    <article><h4>Longest Winning Streaks</h4><ol>{% for row in historical.streaks.single_season_wins limit: 10 %}<li><span>{{ row.rank }}</span><a href="{{ row.path | relative_url }}">{{ row.display_name }}</a><strong>W{{ row.games }}</strong><small>{{ row.start_season }} W{{ row.start_week }}–W{{ row.end_week }}</small></li>{% endfor %}</ol></article>
    <article><h4>Longest Losing Streaks</h4><ol>{% for row in historical.streaks.single_season_losses limit: 10 %}<li><span>{{ row.rank }}</span><a href="{{ row.path | relative_url }}">{{ row.display_name }}</a><strong>L{{ row.games }}</strong><small>{{ row.start_season }} W{{ row.start_week }}–W{{ row.end_week }}</small></li>{% endfor %}</ol></article>
  </div>
</section>

<section class="content-section records-section records-franchise-leaders" id="career-leaderboards" aria-labelledby="career-heading"><div class="wrap">
  <div class="section-heading"><div><p class="eyebrow">Resolved franchise history</p><h2 id="career-heading">Franchise Leaders</h2><p>Season-level totals include verified 2021–2025 standings only where franchise continuity is resolved.</p></div><span class="coverage-badge coverage-badge--partial">{{ historical.franchise_summaries.season_level_coverage.label }}</span></div>
  <div class="record-table-wrap" tabindex="0" role="region" aria-label="Verified season-level franchise totals"><table class="record-table"><thead><tr><th>Rank</th><th>Franchise</th><th>Seasons</th><th>Record</th><th>PF</th><th>PA</th><th>Avg rank</th><th>Titles</th></tr></thead><tbody>
    {% for row in historical.franchise_summaries.franchises %}<tr><td class="record-rank">{{ forloop.index }}</td><td><a class="record-team" href="{{ row.path | relative_url }}"><img src="{{ row.identity_image | relative_url }}" alt="" loading="lazy"><span>{{ row.display_name }}</span></a></td><td>{{ row.season_history.season_count }}</td><td>{{ row.season_history.wins }}–{{ row.season_history.losses }}{% if row.season_history.ties > 0 %}–{{ row.season_history.ties }}{% endif %}</td><td>{{ row.season_history.points_for }}</td><td>{{ row.season_history.points_against }}</td><td>{{ row.season_history.average_final_rank | round: 2 }}</td><td>{{ row.season_history.championships }}</td></tr>{% endfor %}
  </tbody></table></div>
</div></section>

<section class="content-section content-section--navy records-section" id="season-records" aria-labelledby="season-records-heading"><div class="wrap">
  <div class="section-heading section-heading--light"><div><p class="eyebrow">One season. One mark.</p><h2 id="season-records-heading">Season Records</h2><p>Best and lowest verified marks across every final standings row, including unresolved historical names when the season value itself is clear.</p></div><span class="coverage-badge coverage-badge--complete">Results complete</span></div>
  <div class="record-card-grid">
    {% for record in record_book.records.season_results.entries %}<article class="record-card"><p>{{ record.label }}</p><strong>{% if record.format == 'percentage' %}{{ record.holders[0].value | times: 100 | round: 1 }}%{% else %}{{ record.holders[0].value }}{% endif %}</strong><div>{% for holder in record.holders %}<span>{% if holder.path %}<a href="{{ holder.path | relative_url }}">{{ holder.historical_team_name }}</a>{% else %}{{ holder.historical_team_name }}{% endif %} · <a href="{{ holder.season_path | relative_url }}">{{ holder.year }}</a></span>{% endfor %}</div></article>{% endfor %}
    {% for record in record_book.records.season_points.entries %}<article class="record-card"><p>{{ record.label }}</p><strong>{{ record.holders[0].value }}</strong><div>{% for holder in record.holders %}<span>{% if holder.path %}<a href="{{ holder.path | relative_url }}">{{ holder.historical_team_name }}</a>{% else %}{{ holder.historical_team_name }}{% endif %} · <a href="{{ holder.season_path | relative_url }}">{{ holder.year }}</a></span>{% endfor %}</div></article>{% endfor %}
  </div>
  <p class="record-source record-source--dark">Results: complete for 2021–2024 · Scoring: partial while the 2024 PF/PA source conflict remains under review</p>
</div></section>

<section class="shell-content records-section" id="playoff-records" aria-labelledby="playoff-heading">
  {% assign playoff_totals = historical.playoffs.franchises %}
  <div class="section-heading"><div><p class="eyebrow">The championship road</p><h2 id="playoff-heading">Playoff Records</h2><p>Titles and finals use verified 2021–2025 season results. Detailed win/loss and scoring totals use only independently classified 2022–2025 championship-bracket games.</p></div><a class="button button--outline" href="{{ '/cup/' | relative_url }}">Brew Crew Cup</a></div>
  <div class="honor-board-grid">
    <article class="honor-board"><p class="eyebrow">Championships</p><h3>Title Holders</h3>{% for entry in playoff_totals %}{% if entry.championships > 0 %}<div><span class="honor-board__rank">{{ entry.rank }}</span><a href="{{ entry.path | relative_url }}">{{ entry.display_name }}</a><strong>{{ entry.championships }}</strong></div>{% endif %}{% endfor %}<small>Season results · Verified 2021–2025</small></article>
    <article class="honor-board"><p class="eyebrow">Championship appearances</p><h3>Finals Leaders</h3>{% for entry in playoff_totals %}{% if entry.championship_appearances > 0 %}<div><span class="honor-board__rank">{{ entry.rank }}</span><a href="{{ entry.path | relative_url }}">{{ entry.display_name }}</a><strong>{{ entry.championship_appearances }}</strong></div>{% endif %}{% endfor %}<small>Season results · Verified 2021–2025</small></article>
  </div>
  <div class="record-subhead"><div><p class="eyebrow">Verified bracket results</p><h3>Postseason Totals</h3></div><span class="coverage-badge coverage-badge--partial">Partial coverage</span></div>
  <p class="table-scroll-note">Swipe horizontally to see the full leaderboard.</p>
  <div class="record-table-wrap" tabindex="0" role="region" aria-label="Postseason franchise leaderboard"><table class="record-table record-table--compact"><thead><tr><th>Rank</th><th>Franchise</th><th>Games</th><th>Wins</th><th>Losses</th><th>High score</th></tr></thead><tbody>
    {% for entry in playoff_totals %}<tr><td class="record-rank">{{ entry.rank }}</td><td><a class="record-team" href="{{ entry.path | relative_url }}"><img src="{{ entry.identity_image | relative_url }}" alt="" loading="lazy"><span>{{ entry.display_name }}</span></a></td><td>{{ entry.playoff_games }}</td><td>{{ entry.playoff_wins }}</td><td>{{ entry.playoff_losses }}</td><td>{% if entry.highest_playoff_score %}{{ entry.highest_playoff_score }}{% else %}—{% endif %}</td></tr>{% endfor %}
  </tbody></table></div>
  <p class="record-source">{{ historical.playoffs.coverage.label }} · Placement and ambiguous postseason games excluded</p>
  {% assign streaks = record_book.leaderboards.playoff_appearance_streaks %}
  <div class="record-subhead"><div><p class="eyebrow">Inside the verified window</p><h3>Consecutive Playoff Appearances</h3></div></div>
  <div class="streak-grid">{% for entry in streaks.entries limit: 5 %}<article><span>#{{ entry.rank }}</span><div><a href="{{ entry.path | relative_url }}">{{ entry.display_name }}</a><small>{{ entry.start_year }}–{{ entry.end_year }}</small></div><strong>{{ entry.streak }}</strong></article>{% endfor %}</div>
</section>

<section class="content-section records-section records-awaiting" id="awaiting-data" aria-labelledby="awaiting-heading"><div class="wrap">
  <div class="section-heading"><div><p class="eyebrow">Next layers of the archive</p><h2 id="awaiting-heading">Still Being Built</h2><p>These categories stay intentionally empty until the complete source history exists.</p></div></div>
  <div class="unavailable-grid">
    {% for category in record_book.unavailable_categories %}{% if category.category_id == 'playoff_droughts' %}<article class="unavailable-card"><span aria-hidden="true">—</span><div><h3>{{ category.label }}</h3><p>{{ category.message }}</p></div></article>{% endif %}{% endfor %}
    <article class="unavailable-card unavailable-card--bench"><span aria-hidden="true">10</span><div><h3>Bench Blunders</h3><p>Historical bench scoring is still being imported. The Top 10 schema is ready, but no unverified entry will be published.</p></div></article>
  </div>
  <p class="record-method">Every published table carries its source years, source files, coverage state, and generation date in the canonical data. See the <a href="{{ '/history/' | relative_url }}">season archive</a> for the original standings and brackets.</p>
</div></section>
