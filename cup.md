---
layout: default
title: Brew Crew Cup
permalink: /cup/
description: The history and championship tradition of the Road to Glory FFL Brew Crew Cup.
body_class: cup-page
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

<section class="cup-origin" aria-labelledby="olivers-heading"><div class="shell-content cup-origin__grid">
  <div><p class="eyebrow">The people behind the tradition</p><h2 id="olivers-heading">Oliver’s Beverage<br>&amp; the Brew Crew</h2>
    <p><em>From the league’s original Cup archive:</em></p>
    <p>Oliver’s Beverage has been a cornerstone of the Capital Region’s beer scene for decades, earning a reputation as a pioneer in variety and service. Originally established long ago and relocating to its current home on Colvin Avenue in 1987, Oliver’s quickly grew from a modest selection to more than 5,000 varieties of beer from around the world. It was the first in the area to introduce brands like Corona, and at various points carried local favorites like Yuengling Beer and Newman’s Albany Amber.</p>
    <p>In 1989, Oliver’s expanded its reach by acquiring Westmere Beverage on Western Avenue in Guilderland, and together the two stores became known as “The Brew Crew,” a name cemented by their catchy advertising jingle. Over the years, they’ve continued to innovate with offerings like 28 rotating draft lines, crowler machines, growler rewards, keg sales, CO₂ refills, and draft equipment support.</p>
    <p>Their influence on Albany’s beer culture is unmatched, and for 30 years straight they’ve been voted the Best Beer Store in Albany, with Oliver’s often taking the top spot and Westmere right behind. Today, they remain not just retailers, but institutions that have helped shape the region’s love for craft and imported beers.</p>
    <p><strong>Many of the Road To Glory Fantasy Football league members have been integral members of the Brew Crew staff.</strong></p>
    <p><a href="{{ site.data.cup_gallery.source_url }}" target="_blank" rel="noopener noreferrer">Original league history ↗</a> · <a href="https://www.youtube.com/watch?v=scHeJqj9ItU" target="_blank" rel="noopener noreferrer">Watch the archived Brew Crew video ↗</a></p>
  </div>
  <figure><a href="{{ '/assets/img/cup/brew-crew-history.jpg' | relative_url }}"><img src="{{ '/assets/img/cup/brew-crew-history.jpg' | relative_url }}" width="961" height="1366" alt="Brew Crew History artwork featuring a navy football helmet, beer tap, mug, crown, and hops" loading="lazy"></a><figcaption>League history artwork · Open full size</figcaption></figure>
</div></section>

<section class="cup-gallery-section" aria-labelledby="cup-gallery-heading"><div class="shell-content">
  <p class="eyebrow">From the original league photo album</p><h2 id="cup-gallery-heading">Inside the Brew Crew</h2><p>The storefronts, the aisles, and the familiar corners. Select a photograph to view its complete original.</p>
  <div class="cup-gallery">{% for photo in site.data.cup_gallery.images %}<figure><a href="{{ '/assets/img/cup/' | append: photo.file | relative_url }}"><img src="{{ '/assets/img/cup/' | append: photo.file | relative_url }}" alt="{{ photo.alt | escape }}" loading="lazy"></a><figcaption>{{ photo.alt | escape }}</figcaption></figure>{% endfor %}</div>
</div></section>

<section class="shell-content season-section" aria-labelledby="cup-original-heading"><p class="eyebrow">Preserved, not rewritten</p><h2 id="cup-original-heading">The original Cup story</h2>
  <p>“The Cup isn’t just a trophy; it’s a tradition, a piece of league lore, and the ultimate reminder that in the Brew Crew, anyone can be king… for a year.”</p>
  <p class="cup-archive-note">The original poster below records the league through 2024. Its “no one has managed to repeat” line predates Greendale’s second title in 2025; the current Roll of Champions remains authoritative. The inaugural 2021 season had ten teams, rather than the twelve described in the poster.</p>
  <div class="franchise-gallery"><figure class="honors-feature"><a href="{{ '/assets/img/cup/cup-tradition-2024.jpg' | relative_url }}"><img src="{{ '/assets/img/cup/cup-tradition-2024.jpg' | relative_url }}" alt="Original Cup tradition poster and winners list through 2024; historical context explained above" loading="lazy"></a><figcaption>Original championship tradition poster · Open full size</figcaption></figure><figure class="honors-feature"><a href="{{ '/assets/img/cup/brew-crew-wordmark.jpg' | relative_url }}"><img src="{{ '/assets/img/cup/brew-crew-wordmark.jpg' | relative_url }}" alt="Original yellow Brew Crew Cup lettering on a blue background" loading="lazy"></a><figcaption>The original Brew Crew Cup wordmark</figcaption></figure></div>
</section>

<section class="shell-content cup-roll" aria-labelledby="cup-roll-heading">
  <div class="history-intro"><div><p class="eyebrow">The league’s highest honor</p><h2 id="cup-roll-heading">Roll of Champions</h2><p>Five seasons of title games, with each champion’s road to the Cup preserved in the season archive.</p></div></div>
  {% assign champions = site.data.champions.champions | sort: "year" | reverse %}
  <div class="champion-roll">{% for champion in champions %}{% assign title_team = site.data.franchises.franchises | where: "franchise_id", champion.champion_franchise_id | first %}{% assign title_root = '/teams/' %}{% if title_team.status == 'retired' %}{% assign title_root = '/retired/' %}{% endif %}<article><span>{{ champion.year }}</span><a class="champion-roll__identity" href="{{ title_root | append: title_team.slug | append: '/' | relative_url }}"><img src="{{ title_team.branding.identity_image | relative_url }}" alt="{{ title_team.branding.identity_alt | escape }}" loading="lazy"></a><div><h3><a href="{{ title_root | append: title_team.slug | append: '/' | relative_url }}">{{ champion.champion_display_name }}</a></h3><p>{{ champion.champion_score }}–{{ champion.runner_up_score }} over {{ champion.runner_up_display_name }}</p></div><a class="text-link" href="{{ champion.season_path | relative_url }}">Season archive <span aria-hidden="true">→</span></a></article>{% endfor %}</div>
  <p><a class="button button--outline" href="{{ '/championships/' | relative_url }}">Explore championship statistics</a></p>
</section>
