---
layout: default
title: Drafts
permalink: /drafts/
description: Verified Road to Glory FFL draft orders, original results, and recap archive.
---

{% include page-hero.html eyebrow="Where seasons begin" title="Draft Archive" description="The verified order and original results from every Road to Glory draft currently preserved by the public league archive." compact=true %}

<section class="shell-content draft-archive" aria-labelledby="draft-archive-heading">
  <div class="history-intro">
    <div><p class="eyebrow">On the clock</p><h2 id="draft-archive-heading">Built pick by pick</h2></div>
    <p>Each archive page preserves the historical team names shown that season, while resolved identities connect back to the franchise record. Select any result image to inspect it at full size.</p>
  </div>

  <div class="draft-archive-grid">
    {% assign drafts = site.data.drafts.drafts | sort: "year" | reverse %}
    {% for draft in drafts %}
      <article class="draft-season-card">
        <a class="draft-season-card__image" href="{{ '/drafts/' | append: draft.year | append: '/' | relative_url }}">
          <img src="{{ draft.results_assets[0].path | relative_url }}" alt="Preview of {{ draft.year }} Road to Glory draft results">
          <span>{{ draft.year }}</span>
        </a>
        <div class="draft-season-card__body">
          <p class="eyebrow">Draft archive</p>
          <h2><a href="{{ '/drafts/' | append: draft.year | append: '/' | relative_url }}">{{ draft.year }} Draft</a></h2>
          <dl>
            <div><dt>Teams</dt><dd>{{ draft.team_count }}</dd></div>
            <div><dt>Rounds</dt><dd>{{ draft.rounds }}</dd></div>
            {% if draft.draft_date %}<div><dt>Date</dt><dd>{{ draft.draft_date | date: "%B %-d, %Y" }}</dd></div>{% endif %}
          </dl>
          <a class="text-link" href="{{ '/drafts/' | append: draft.year | append: '/' | relative_url }}">Open draft archive <span aria-hidden="true">→</span></a>
        </div>
      </article>
    {% endfor %}
  </div>
</section>
