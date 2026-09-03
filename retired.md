---
layout: default
title: Retired Franchises
permalink: /retired/
description: Retired Road to Glory FFL franchises and preserved historical team identities.
---

{% assign retired_franchises = site.data.franchises.franchises | where: "status", "retired" %}
{% include page-hero.html eyebrow="Never forgotten" title="Franchise Archive" description="Preserving retired franchises and earlier identities that remain part of active franchise history." compact=true %}

<section class="content-section content-section--tight">
  <div class="wrap team-directory-intro">
    <div>
      <p class="eyebrow eyebrow--dark">League archive</p>
      <h2>History beyond today's team names</h2>
      <p>Retired franchises and former identities keep their public stories, owners, rivalries, and original team art in the Road to Glory archive.</p>
    </div>
    <a class="button button--gold" href="{{ '/teams/' | relative_url }}">Active teams</a>
  </div>
</section>

<section class="content-section content-section--navy">
  <div class="wrap retired-grid">
    {% for franchise in retired_franchises %}
      <article class="retired-card" data-archive-kind="retired-franchise">
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

    <article class="retired-card" data-archive-kind="historical-identity">
      <a class="retired-card__image" href="{{ '/retired/quahog-stripes/' | relative_url }}">
        <img src="{{ '/assets/img/franchises/quahog-stripes/identity.jpg' | relative_url }}" alt="White Quahog Stripes football helmet with an orange animal emblem" loading="lazy">
      </a>
      <div class="retired-card__body">
        <p class="eyebrow">Historical identity · 2021–2022</p>
        <h2><a href="{{ '/retired/quahog-stripes/' | relative_url }}">Quahog Stripes</a></h2>
        <p>The original identity of the franchise now known as the New Jersey Giants, preserved with its historical name and artwork.</p>
        <a class="button button--outline-light" href="{{ '/retired/quahog-stripes/' | relative_url }}">Open identity archive</a>
      </div>
    </article>
  </div>
</section>
