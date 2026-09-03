---
layout: default
title: League History
permalink: /history/
description: Road to Glory FFL seasons, standings, playoffs, championships, and stories.
---

{% include page-hero.html eyebrow="The complete story" title="League History" description="Season standings, playoff brackets, championship stories, and defining moments from across Road to Glory history." compact=true %}

<section class="shell-content">
  <div class="history-intro"><div><p class="eyebrow">Five seasons. Four champions.</p><h2>Every Road Leaves a Record</h2><p>The archive preserves verified final standings, playoff paths, title-game scores, weekly results where available, and approved league artwork from 2021 through 2025.</p></div><a class="button button--gold" href="{{ '/cup/' | relative_url }}">See the Cup roll of honor</a></div>

  {% assign seasons = site.data.seasons.seasons | sort: "year" | reverse %}
  <div class="season-archive-grid">
    {% for season in seasons %}
      {% assign champion = site.data.franchises.franchises | where: "franchise_id", season.champion_franchise_id | first %}
      {% assign final = site.data.champions.champions | where: "year", season.year | first %}
      {% assign story = site.data.generated.recaps.seasons | where: "season", season.year | first %}
      <article class="season-archive-card">
        <a class="season-archive-card__image" href="{{ '/history/' | append: season.year | append: '/' | relative_url }}"><img src="{{ champion.branding.identity_image | relative_url }}" alt="{{ champion.branding.identity_alt }}"></a>
        <div class="season-archive-card__body"><p class="eyebrow">{{ season.year }} champion</p><h2><a href="{{ '/history/' | append: season.year | append: '/' | relative_url }}">{{ season.champion_display_name }}</a></h2><p>{{ story.summary }}</p>{% if story.best_record_display %}<p class="season-archive-card__best"><strong>Best record</strong> {{ story.best_record_display }}</p>{% endif %}<div><span>{{ season.team_count }} teams</span><a class="text-link" href="{{ '/history/' | append: season.year | append: '/' | relative_url }}">Full season story <span aria-hidden="true">→</span></a></div></div>
      </article>
    {% endfor %}
  </div>
</section>
