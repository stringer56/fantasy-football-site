---
layout: default
title: League History
permalink: /history/
description: Road to Glory FFL seasons, standings, playoffs, championships, and stories.
---

{% include page-hero.html eyebrow="The complete story" title="League History" description="Season standings, playoff brackets, championship stories, and defining moments from across Road to Glory history." compact=true %}

<section class="shell-content">
  <div class="history-intro"><div><p class="eyebrow">Five seasons. Four champions.</p><h2>Every Road Leaves a Record</h2><p>The archive preserves verified final standings, playoff paths, title-game scores, weekly results where available, and approved league artwork from 2021 through 2025.</p></div><div class="championship-links"><a class="button button--gold" href="{{ '/cup/' | relative_url }}">See the Cup roll of honor</a><a class="button button--outline" href="{{ '/all-time-standings/' | relative_url }}">Explore all-time statistics</a></div></div>

  {% assign seasons = site.data.seasons.seasons | sort: "year" | reverse %}
  <div class="season-archive-grid">
    {% for archive_season in seasons %}{% include champion-card.html season=archive_season %}{% endfor %}
  </div>
</section>
