---
layout: default
title: Teams & Owners
permalink: /teams/
description: Active Road to Glory FFL franchises, owners, identities, and rivalries.
---

{% assign active_franchises = site.data.franchises.franchises | where: "status", "active" %}
<header class="directory-hero"><div class="wrap">
  <div><p class="eyebrow">The Road to Glory roster</p><h1>Teams &amp; Owners</h1><p>Twelve identities. A league of rivalries. One Brew Crew Cup.</p></div>
  <div class="directory-hero__edition"><strong>{{ active_franchises.size }}</strong><span>Active franchises</span><a href="{{ '/retired/' | relative_url }}">Explore the retired archive →</a></div>
</div></header>
<section class="content-section content-section--neutral" aria-label="Active franchises">
  <div class="wrap franchise-card-grid">
    {% for franchise in active_franchises %}{% include franchise-card.html franchise=franchise %}{% endfor %}
  </div>
</section>
