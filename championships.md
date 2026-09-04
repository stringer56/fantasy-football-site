---
layout: default
title: Championship History
permalink: /championships/
description: Verified Road to Glory championship games and franchise title records from 2021 through 2025.
---

{% assign data = site.data.generated.records.championships %}

{% include page-hero.html eyebrow="Brew Crew Cup · 2021–2025" title="Championship History" description="Five verified finals, one continuous franchise record, and no duplicate identities when teams changed names." compact=true %}

<nav class="records-jump" aria-label="Historical statistics sections"><div class="wrap"><a href="{{ '/all-time-standings/' | relative_url }}">Standings</a><a href="{{ '/head-to-head/' | relative_url }}">Head-to-Head</a><a href="{{ '/records/' | relative_url }}">Record Book</a><a href="{{ '/championships/' | relative_url }}" aria-current="page">Championships</a></div></nav>

<section class="shell-content records-section" aria-labelledby="championship-history-heading">
  <div class="section-heading"><div><p class="eyebrow">The complete verified finals</p><h2 id="championship-history-heading">Championship Results</h2><p>Seeds appear only where the season archive verifies them.</p></div><span class="coverage-badge coverage-badge--complete">{{ data.coverage.label }}</span></div>
  <p class="table-scroll-note">Swipe horizontally to see every championship field.</p>
  <div class="record-table-wrap" tabindex="0" role="region" aria-label="Verified Road to Glory championship history">
    <table class="record-table record-table--championships"><thead><tr><th>Year</th><th>Champion</th><th>Runner-Up</th><th>Score</th><th>Margin</th><th>Seeds</th></tr></thead><tbody>
      {% for final in data.championships %}<tr>
        <td class="record-rank"><a href="{{ final.season_path | relative_url }}">{{ final.season }}</a></td>
        <td><a href="{{ final.champion.path | relative_url }}">{{ final.champion.display_name }}</a></td>
        <td><a href="{{ final.runner_up.path | relative_url }}">{{ final.runner_up.display_name }}</a></td>
        <td>{{ final.champion_score }}–{{ final.runner_up_score }}</td><td>{{ final.margin }}</td>
        <td>{% if final.champion_seed %}#{{ final.champion_seed }} / {% else %}— / {% endif %}{% if final.runner_up_seed %}#{{ final.runner_up_seed }}{% else %}—{% endif %}</td>
      </tr>{% endfor %}
    </tbody></table>
  </div>
</section>

<section class="content-section content-section--navy records-section" aria-labelledby="championship-leaders-heading"><div class="wrap">
  <div class="section-heading section-heading--light"><div><p class="eyebrow">Franchise honors</p><h2 id="championship-leaders-heading">Championship Leaders</h2><p>Historical aliases consolidate under stable franchise identities.</p></div></div>
  <div class="championship-leader-grid">
    <article class="honor-board"><p class="eyebrow">Most championships</p><h3>Title Leaders</h3>{% for row in data.leaderboards.most_championships %}{% if row.championships > 0 %}<div><span class="honor-board__rank">{{ row.rank }}</span><a href="{{ row.path | relative_url }}">{{ row.display_name }}</a><strong>{{ row.championships }}</strong></div>{% endif %}{% endfor %}</article>
    <article class="honor-board"><p class="eyebrow">Most appearances</p><h3>Finals Leaders</h3>{% for row in data.leaderboards.most_appearances %}<div><span class="honor-board__rank">{{ row.rank }}</span><a href="{{ row.path | relative_url }}">{{ row.display_name }}</a><strong>{{ row.appearances }}</strong></div>{% endfor %}</article>
    <article class="honor-board"><p class="eyebrow">Championship record</p><h3>Finals Win Rate</h3>{% for row in data.leaderboards.best_championship_record %}<div><span class="honor-board__rank">{{ row.rank }}</span><a href="{{ row.path | relative_url }}">{{ row.display_name }}</a><strong>{{ row.championships }}–{{ row.runner_up_finishes }}</strong></div>{% endfor %}</article>
    <article class="honor-board"><p class="eyebrow">Runner-up finishes</p><h3>Second Place</h3>{% for row in data.leaderboards.most_runner_up_finishes %}{% if row.runner_up_finishes > 0 %}<div><span class="honor-board__rank">{{ row.rank }}</span><a href="{{ row.path | relative_url }}">{{ row.display_name }}</a><strong>{{ row.runner_up_finishes }}</strong></div>{% endif %}{% endfor %}</article>
  </div>
  <p class="record-source record-source--dark">{{ data.coverage.label }} · Placement games are not championship appearances.</p>
</div></section>

<section class="shell-content records-section championship-links" aria-label="Championship archive links"><a class="button button--gold" href="{{ '/cup/' | relative_url }}">Brew Crew Cup</a><a class="button button--outline" href="{{ '/history/' | relative_url }}">Season Archive</a></section>
