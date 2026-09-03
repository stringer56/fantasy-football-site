---
layout: default
title: Head-to-Head
permalink: /head-to-head/
description: Compare verified Road to Glory franchise matchup history from 2022 through 2025.
---

{% assign h2h = site.data.generated.records.head_to_head %}
{% assign summaries = site.data.generated.records.franchise_summaries.franchises %}

{% include page-hero.html eyebrow="Franchise matchups" title="Head-to-Head" description="Choose two franchises to open their verified Yahoo matchup history. Results cover 2022–2025 and never assign unresolved historical identities." compact=true %}

<section class="shell-content h2h-shell" data-h2h-app data-baseurl="{{ site.baseurl }}">
  <div class="section-heading">
    <div><p class="eyebrow">Build the matchup</p><h2>Compare two franchises</h2><p>Regular-season and postseason meetings are included; championship-playoff totals use only independently classified bracket games.</p></div>
    <span class="coverage-badge coverage-badge--partial">{{ h2h.coverage.label }}</span>
  </div>
  <div class="h2h-controls">
    <label for="franchise-a">Franchise A<select id="franchise-a" data-h2h-a><option value="">Select a franchise</option>{% for team in summaries %}<option value="{{ team.franchise_id }}">{{ team.display_name }}</option>{% endfor %}</select></label>
    <span aria-hidden="true">vs</span>
    <label for="franchise-b">Franchise B<select id="franchise-b" data-h2h-b><option value="">Select a franchise</option>{% for team in summaries %}<option value="{{ team.franchise_id }}">{{ team.display_name }}</option>{% endfor %}</select></label>
  </div>
  <div class="h2h-result" data-h2h-result aria-live="polite">
    <div class="empty-state"><span class="empty-state__mark" aria-hidden="true">H2H</span><div><h3>Select two franchises</h3><p>The verified series record will appear here.</p></div></div>
  </div>
</section>

<script type="application/json" id="h2h-data">{{ h2h | jsonify }}</script>
<script src="{{ '/assets/js/head-to-head.js' | relative_url }}" defer></script>
