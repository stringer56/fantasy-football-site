---
layout: default
title: Head-to-Head
permalink: /head-to-head/
description: Compare verified Road to Glory franchise matchup history from 2021 through 2025.
---

{% assign h2h = site.data.generated.records.head_to_head %}
{% assign summaries = site.data.generated.records.franchise_career.franchises %}

{% include page-hero.html eyebrow="Verified League History — 2021–2025" title="Head-to-Head" description="Choose two franchises to open the complete verified series. Historical aliases stay consolidated under their canonical teams." compact=true %}

<nav class="records-jump" aria-label="Historical statistics sections"><div class="wrap"><a href="{{ '/all-time-standings/' | relative_url }}">Standings</a><a href="{{ '/head-to-head/' | relative_url }}" aria-current="page">Head-to-Head</a><a href="{{ '/records/' | relative_url }}">Record Book</a><a href="{{ '/championships/' | relative_url }}">Championships</a></div></nav>

<section class="shell-content h2h-shell" data-h2h-app data-baseurl="{{ site.baseurl }}">
  <div class="section-heading">
    <div><p class="eyebrow">Build the matchup</p><h2>Compare two franchises</h2><p>All verified meetings are included. Playoff and championship totals count only independently classified championship-bracket games.</p></div>
    <span class="coverage-badge coverage-badge--complete">{{ h2h.coverage.label }}</span>
  </div>
  <div class="h2h-controls">
    <label for="franchise-a">Franchise A<select id="franchise-a" data-h2h-a><option value="">Select a franchise</option>{% for team in summaries %}<option value="{{ team.franchise_id }}">{{ team.display_name }}</option>{% endfor %}</select></label>
    <span aria-hidden="true">vs</span>
    <label for="franchise-b">Franchise B<select id="franchise-b" data-h2h-b><option value="">Select a franchise</option>{% for team in summaries %}<option value="{{ team.franchise_id }}">{{ team.display_name }}</option>{% endfor %}</select></label>
  </div>
  <div class="h2h-result" data-h2h-result aria-live="polite">
    <div class="empty-state"><span class="empty-state__mark" aria-hidden="true">H2H</span><div><h3>Select two franchises</h3><p>The complete 2021–2025 series will appear here. Your selection becomes a shareable URL.</p></div></div>
  </div>
</section>

<script type="application/json" id="h2h-data">{{ h2h | jsonify }}</script>
<script src="{{ '/assets/js/head-to-head.js' | relative_url }}" defer></script>
