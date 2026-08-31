---
layout: default
title: Retired Franchises
permalink: /retired/
description: Retired Road to Glory FFL franchises and their preserved league history.
---

{% assign retired_franchises = site.data.franchises.franchises | where: "status", "retired" %}
{% include page-hero.html eyebrow="Never forgotten" title="Retired Franchises" description="Preserving the names, owners, records, and stories of franchises no longer active in Road to Glory." compact=true %}

<section class="content-section content-section--tight">
  <div class="wrap team-directory-intro">
    <div>
      <p class="eyebrow eyebrow--dark">League archive</p>
      <h2>History beyond the active roster</h2>
      <p>These franchises are no longer active, but their names, public stories, owners, rivalries, and original team art remain part of Road to Glory.</p>
    </div>
    <a class="button button--gold" href="{{ '/teams/' | relative_url }}">Active teams</a>
  </div>
</section>

<section class="content-section content-section--navy">
  <div class="wrap retired-grid">
    {% for franchise in retired_franchises %}
      <article class="retired-card">
        <a class="retired-card__image" href="{{ '/retired/' | append: franchise.slug | append: '/' | relative_url }}">
          <img src="{{ franchise.branding.identity_image | relative_url }}" alt="{{ franchise.branding.identity_alt | escape }}" loading="lazy">
        </a>
        <div class="retired-card__body">
          <p class="eyebrow">Retired franchise</p>
          <h2><a href="{{ '/retired/' | append: franchise.slug | append: '/' | relative_url }}">{{ franchise.name }}</a></h2>
          <p>{{ franchise.profile.summary }}</p>
          <a class="button button--outline-light" href="{{ '/retired/' | append: franchise.slug | append: '/' | relative_url }}">Open archive profile</a>
        </div>
      </article>
    {% endfor %}
  </div>
</section>
