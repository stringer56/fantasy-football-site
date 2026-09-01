---
layout: default
title: Manager Power Rankings
permalink: /votes/power-rankings/
description: Weekly manager-voted Road to Glory FFL Power Rankings.
---

{% assign power = site.data.generated.power_rankings %}
{% include page-hero.html eyebrow="Twelve ballots. One order." title="Manager Power Rankings" description="Every manager ranks every active franchise. No standings formula, projections, or hidden algorithm enters the vote." compact=true %}

<section class="shell-content vote-section">
  <div class="ranking-method"><div><p class="eyebrow">The ballot</p><h2>Purely Manager Voted</h2><p>With twelve active teams, first place earns 12 points, second earns 11, and twelfth earns 1. Ties break by first-place votes, average rank, then franchise ID only as a stable final display fallback.</p></div><dl><div><dt>Season</dt><dd>{{ power.season }}</dd></div><div><dt>Week</dt><dd>{% if power.week %}{{ power.week }}{% else %}—{% endif %}</dd></div><div><dt>Ballots</dt><dd>{{ power.ballots_counted }}</dd></div></dl></div>

  {% if power.rankings.size > 0 %}
    <p class="table-scroll-note">Swipe horizontally to see every ranking field.</p><div class="vote-table-wrap" role="region" aria-label="Manager-voted Power Rankings" tabindex="0"><table class="vote-table power-table"><thead><tr><th>Rank</th><th>Franchise</th><th>Movement</th><th>Points</th><th>Average</th><th>Firsts</th><th>Ballots</th></tr></thead><tbody>{% for team in power.rankings %}<tr><td class="vote-rank">{{ team.rank }}</td><td><a class="vote-team" href="{{ team.path | relative_url }}"><img src="{{ team.identity_image | relative_url }}" alt=""><span>{{ team.display_name }}</span></a></td><td>{% if team.movement == null %}—{% elsif team.movement > 0 %}<span class="movement movement--up">↑ {{ team.movement }}</span>{% elsif team.movement < 0 %}<span class="movement movement--down">↓ {{ team.movement | abs }}</span>{% else %}<span class="movement">—</span>{% endif %}</td><td>{{ team.total_points }}</td><td>{{ team.average_rank }}</td><td>{{ team.first_place_votes }}</td><td>{{ team.ballots_counted }}</td></tr>{% endfor %}</tbody></table></div>
  {% else %}
    <div class="vote-empty"><span aria-hidden="true">12</span><div><h3>Voting opens during the season.</h3><p>No ballots have been imported, so no ranking order or movement is shown.</p></div></div>
  {% endif %}
  <div class="vote-back-links"><a class="text-link" href="{{ '/votes/' | relative_url }}"><span aria-hidden="true">←</span> League Votes</a><a class="text-link" href="{{ '/teams/' | relative_url }}">Meet the franchises <span aria-hidden="true">→</span></a></div>
</section>
