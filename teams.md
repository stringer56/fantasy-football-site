---
layout: default
title: Teams & Owners
permalink: /teams/
description: Active Road to Glory FFL franchises, owners, identities, and rivalries.
---

{% assign active_franchises = site.data.franchises.franchises | where: "status", "active" %}
{% include page-hero.html eyebrow="The league" title="Teams & Owners" description="The franchises, managers, identities, and rivalries that make Road to Glory what it is." compact=true %}

<section class="content-section content-section--tight">
  <div class="wrap team-directory-intro">
    <div>
      <p class="eyebrow eyebrow--dark">Franchise headquarters</p>
      <h2>{{ active_franchises.size }} teams. One cup.</h2>
      <p>Every current franchise now has a stable identity that survives Yahoo name changes. Open a profile for its coach, league story, rivalries, home field, and original team art.</p>
    </div>
    <a class="button button--gold" href="{{ '/retired/' | relative_url }}">Retired archive</a>
  </div>
</section>

<section class="content-section content-section--neutral content-section--bordered">
  <div class="wrap franchise-card-grid">
    {% for franchise in active_franchises %}
      <article class="franchise-card">
        <a class="franchise-card__image" href="{{ '/teams/' | append: franchise.slug | append: '/' | relative_url }}">
          <img src="{{ franchise.branding.identity_image | relative_url }}" alt="{{ franchise.branding.identity_alt | escape }}" loading="lazy">
        </a>
        <div class="franchise-card__body">
          <p class="franchise-card__status">Active franchise</p>
          <h2><a href="{{ '/teams/' | append: franchise.slug | append: '/' | relative_url }}">{{ franchise.name }}</a></h2>
          <p class="franchise-card__owner">Coach {% for owner_id in franchise.owner_ids %}{% assign owner = site.data.owners.owners | where: "owner_id", owner_id | first %}{% if owner %}{{ owner.display_name }}{% unless forloop.last %}, {% endunless %}{% endif %}{% endfor %}</p>
          <p>{{ franchise.profile.summary | truncate: 150 }}</p>
          <div class="franchise-card__footer">
            <span>{% if franchise.profile.championship_seasons.size > 0 %}Champion {{ franchise.profile.championship_seasons | join: ', ' }}{% else %}Chasing glory{% endif %}</span>
            <a class="text-link" href="{{ '/teams/' | append: franchise.slug | append: '/' | relative_url }}">Team profile <span aria-hidden="true">→</span></a>
          </div>
        </div>
      </article>
    {% endfor %}
  </div>
</section>
