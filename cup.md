---
layout: default
title: Brew Crew Cup
permalink: /cup/
description: The history and championship tradition of the Road to Glory FFL Brew Crew Cup.
---

{% include page-hero.html eyebrow="League immortality" title="Brew Crew Cup" description="The trophy, the title games, and the championship runs at the heart of Road to Glory." compact=true %}

<section class="shell-content">
  <div class="history-intro"><div><p class="eyebrow">The league’s highest honor</p><h2>Roll of Champions</h2><p>Every entry below comes from the canonical championship record and links to its complete season archive.</p></div></div>
  {% assign champions = site.data.champions.champions | sort: "year" | reverse %}
  <div class="champion-roll">{% for champion in champions %}<article><span>{{ champion.year }}</span><div><h3>{{ champion.champion_display_name }}</h3><p>{{ champion.champion_score }}–{{ champion.runner_up_score }} over {{ champion.runner_up_display_name }}</p></div><a class="text-link" href="{{ champion.season_path | relative_url }}">Season archive <span aria-hidden="true">→</span></a></article>{% endfor %}</div>
</section>
