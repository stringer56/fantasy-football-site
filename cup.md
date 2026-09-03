---
layout: default
title: Brew Crew Cup
permalink: /cup/
description: The history and championship tradition of the Road to Glory FFL Brew Crew Cup.
---

{% include page-hero.html eyebrow="League immortality" title="Brew Crew Cup" description="The trophy, the title games, and the championship runs at the heart of Road to Glory." compact=true %}

<section class="shell-content cup-trophy-feature" aria-labelledby="cup-story-heading">
  <figure class="cup-trophy-feature__photo">
    <img src="{{ '/assets/img/cup/brew-crew-cup.jpg' | relative_url }}" alt="The gold Brew Crew Cup trophy displayed against a stone wall">
    <figcaption>The Brew Crew Cup · Road to Glory’s traveling championship trophy</figcaption>
  </figure>
  <div class="cup-trophy-feature__story">
    <p class="eyebrow">One cup. One year of bragging rights.</p>
    <h2 id="cup-story-heading">The prize at the end of the road</h2>
    <p>The Brew Crew Cup is the league’s symbol of fantasy-football supremacy. After the regular season and playoff bracket, one franchise earns the right to put its name into league history.</p>
    <p>The champion’s name and team are engraved on the trophy before the Cup travels to its new home. It stays with the winner until the next champion claims it, turning every season into another chapter of the same league tradition.</p>
    <dl class="cup-trophy-feature__facts">
      <div><dt>Introduced</dt><dd>2021</dd></div>
      <div><dt>First five seasons</dt><dd>4 different champions</dd></div>
      <div><dt>Tradition</dt><dd>Engraved &amp; shipped to the winner</dd></div>
    </dl>
  </div>
</section>

<section class="cup-banner" aria-label="Brew Crew Cup history artwork">
  <div class="shell-content"><img src="{{ '/assets/img/cup/brew-crew-history.jpg' | relative_url }}" alt="Brew Crew History artwork featuring a navy football helmet, beer tap, mug, crown, and hops"></div>
</section>

<section class="shell-content cup-roll" aria-labelledby="cup-roll-heading">
  <div class="history-intro"><div><p class="eyebrow">The league’s highest honor</p><h2 id="cup-roll-heading">Roll of Champions</h2><p>Every entry below comes from the canonical championship record and links to its complete season archive.</p></div></div>
  {% assign champions = site.data.champions.champions | sort: "year" | reverse %}
  <div class="champion-roll">{% for champion in champions %}<article><span>{{ champion.year }}</span><div><h3>{{ champion.champion_display_name }}</h3><p>{{ champion.champion_score }}–{{ champion.runner_up_score }} over {{ champion.runner_up_display_name }}</p></div><a class="text-link" href="{{ champion.season_path | relative_url }}">Season archive <span aria-hidden="true">→</span></a></article>{% endfor %}</div>
</section>
