---
layout: default
title: Home
description: Road to Glory FFL league headquarters—2026 standings, weekly matchups, franchise stories, and the pursuit of the Brew Crew Cup.
body_class: home-page
---

{% assign live = site.data.generated.live_season %}
{% assign latest_champion = site.data.champions.champions | sort: 'year' | last %}
{% assign active = site.data.franchises.franchises | where: 'status', 'active' %}
<section class="home-hero"><div class="wrap home-hero__inner">
  <div><p class="eyebrow">{{ site.data.site.current_season }} season · Established {{ site.data.league.founded_season }}</p>
    <h1>Road to<br>Glory <span>Fantasy Football League</span></h1>
    <p class="home-hero__lede">Twelve franchises. A league of rivalries.<br>One Brew Crew Cup.</p>
    <div class="hero-actions"><a class="button button--gold" href="{{ '/2026/' | relative_url }}">2026 League HQ →</a><a class="button button--outline-light" href="#weekly-matchups">This week’s matchups</a></div>
    <a class="home-yahoo-link" href="{{ site.data.site.yahoo.league_url }}" target="_blank" rel="noopener noreferrer">View League on Yahoo ↗</a>
  </div>
  <figure class="home-trophy"><img src="{{ '/assets/img/cup/brew-crew-cup.jpg' | relative_url }}" width="1536" height="2048" alt="The league’s gold Brew Crew Cup trophy" fetchpriority="high">
    <figcaption><span>The prize that brings us back</span><strong>Brew Crew Cup</strong>{% if latest_champion %}<a href="{{ latest_champion.season_path | relative_url }}">{{ latest_champion.year }} champions · {{ latest_champion.champion_display_name }} ↗</a>{% endif %}</figcaption>
  </figure>
</div></section>

<aside class="news-strip" aria-label="NFL and fantasy news"><div class="wrap news-strip__inner"><div class="news-strip__title">NFL + Fantasy Wire</div><div class="ticker-viewport">{% if site.data.news.items.size > 0 %}<div class="ticker">{% for item in site.data.news.items %}<span class="ticker__item"><span class="ticker__source">{{ item.source }}</span><a href="{{ item.link }}" target="_blank" rel="noopener noreferrer">{{ item.title }}</a></span>{% endfor %}<span aria-hidden="true">{% for item in site.data.news.items %}<span class="ticker__item"><span class="ticker__source">{{ item.source }}</span><a href="{{ item.link }}" tabindex="-1" target="_blank" rel="noopener noreferrer">{{ item.title }}</a></span>{% endfor %}</span></div>{% else %}<div class="news-empty">NFL and fantasy headlines return with the next update.</div>{% endif %}</div></div></aside>

<section class="content-section home-live" aria-labelledby="home-live-heading"><div class="wrap">
  <div class="section-heading"><div><p class="eyebrow">The current season</p><h2 id="home-live-heading">2026 League Pulse</h2></div><div class="home-live__freshness"><span class="data-state{% if live.data_status == 'stale' %} data-state--stale{% endif %}">{% if live.data_status == 'ready' %}Current{% elsif live.data_status == 'stale' %}Last available snapshot{% else %}Unavailable{% endif %}</span>{% if live.freshness.source_updated_at %}<time datetime="{{ live.freshness.source_updated_at }}" data-freshness="{{ live.freshness.source_updated_at }}">{{ live.freshness.source_updated_at | date: '%b %-d · %-I:%M %p' }}</time>{% endif %}</div></div>
  <p class="source-caption">{% if site.data.generated.manifest.source == 'official_yahoo_public_page_fallback' %}Yahoo public-page snapshot · API feed unavailable{% else %}Yahoo season snapshot{% endif %} · Scores and standings are separate from manager voting.</p>
  <div class="pulse-grid">
    <article class="home-live-card home-live-card--featured"><div class="home-live-card__heading"><span>Week {{ live.current_week }}</span><a href="{{ '/2026/' | relative_url }}">Season HQ →</a></div>
      {% if live.featured_matchup %}<h3>Featured Matchup</h3><div class="home-featured-matchup">{% for team in live.featured_matchup.teams %}<div><a href="{{ team.path | relative_url }}"><img src="{{ team.identity_image | relative_url }}" alt="" loading="lazy"><strong>{{ team.short_name }}</strong></a><span>{% if team.score != null %}{{ team.score | round: 2 }}{% else %}—{% endif %}</span>{% if team.projected_score != null %}<small>Proj. {{ team.projected_score | round: 2 }}</small>{% endif %}</div>{% unless forloop.last %}<b>VS</b>{% endunless %}{% endfor %}</div><small class="home-featured-matchup__status">{{ live.featured_matchup.status_label }}</small>{% else %}<p>The weekly slate will appear here when available.</p>{% endif %}
    </article>
    <article class="home-live-card"><div class="home-live-card__heading"><span>Standings</span><a href="{{ '/2026/#standings' | relative_url }}">All twelve →</a></div><ol class="home-standings-top">{% for team in live.standings limit: 6 %}<li><span>{{ team.rank | default: '—' }}</span><img src="{{ team.identity_image | relative_url }}" alt="" loading="lazy"><a href="{{ team.path | relative_url }}">{{ team.short_name }}</a><strong>{{ team.wins }}–{{ team.losses }}–{{ team.ties }}</strong></li>{% endfor %}</ol>{% if live.standings.size == 0 %}<p>Standings will return with the next available snapshot.</p>{% endif %}</article>
    <aside class="pulse-wire"><p class="eyebrow">Road to Glory Wire</p><h3>Inside the league</h3>{% for headline in live.league_wire limit: 3 %}<div><h4>{{ headline.headline }}</h4><p>{{ headline.detail }}</p></div>{% else %}<p>League headlines return when there is news to report.</p>{% endfor %}<a class="text-link" href="{{ '/2026/#league-wire' | relative_url }}">All league headlines →</a>{% if live.record_watch.size > 0 %}{% include record-watch.html alerts=live.record_watch %}{% endif %}</aside>
  </div>
</div></section>

<section class="content-section content-section--neutral" id="weekly-matchups" aria-labelledby="home-matchups-heading"><div class="wrap">
  {% assign weekly_hub = '/2026/' %}{% if live.current_week %}{% assign weekly_hub = '/2026/week/' | append: live.current_week | append: '/' %}{% endif %}
  {% include section-heading.html id="home-matchups-heading" eyebrow="The weekly slate" title="This Week’s Matchups" href=weekly_hub link_text="Weekly hub" %}
  {% if live.matchups.size > 0 %}<div class="live-matchup-grid home-matchup-grid">{% for matchup in live.matchups %}{% include live-matchup-card.html matchup=matchup %}{% endfor %}</div>{% else %}<p>The next slate will appear when the schedule is available.</p>{% endif %}
</div></section>

<section class="content-section"><div class="wrap"><div class="cup-feature"><img class="cup-feature__art" src="{{ '/assets/img/cup/brew-crew-history.jpg' | relative_url }}" alt="Brew Crew History artwork featuring a football helmet and beer tap" loading="lazy"><div><p class="eyebrow">League immortality</p><h2>The Brew Crew <span>Cup</span></h2><p>Every draft, rivalry, and playoff run leads to one prize. Meet the champions and trace the history of the league’s traveling trophy.</p><a class="button button--gold" href="{{ '/cup/' | relative_url }}">The Cup &amp; its champions →</a></div></div></div></section>

<section class="content-section content-section--neutral" aria-labelledby="home-franchises-heading"><div class="wrap">
  {% include section-heading.html id="home-franchises-heading" eyebrow="Know your rivals" title="The Franchises" href="/teams/" link_text="Teams & owners" %}
  <div class="franchise-strip" tabindex="0" role="region" aria-label="All twelve franchise profiles; scroll horizontally">
    {% for team in active %}<a href="{{ '/teams/' | append: team.slug | append: '/' | relative_url }}" style="--team-accent: {{ team.branding.primary_color }}"><img src="{{ team.branding.identity_image | relative_url }}" alt="" loading="lazy"><strong>{{ team.name }}</strong><span>Team profile →</span></a>{% endfor %}
  </div>
</div></section>

<section class="content-section" aria-labelledby="home-history-heading"><div class="wrap">
  {% include section-heading.html id="home-history-heading" eyebrow="Written in league history" title="Recent Champions" href="/history/" link_text="Every season" %}
  {% assign recent_seasons = site.data.seasons.seasons | sort: 'year' | reverse %}
  <div class="recent-champions">{% for archived_season in recent_seasons limit: 3 %}{% include champion-card.html season=archived_season compact=true %}{% endfor %}</div>
</div></section>

<section class="content-section content-section--navy" aria-labelledby="home-records-heading"><div class="wrap">
  <div class="section-heading section-heading--light"><div><p class="eyebrow">Verified 2021–2025</p><h2 id="home-records-heading">The Marks to Beat</h2></div><a class="button button--outline-light" href="{{ '/records/' | relative_url }}">Open the record book →</a></div>
  {% include record-spotlights.html %}
</div></section>

<section class="content-section" aria-labelledby="home-draft-heading"><div class="wrap draft-desk">
  {% assign latest_draft = site.data.drafts.drafts | sort: 'year' | last %}
  <div><p class="eyebrow">On the clock</p><h2 id="home-draft-heading">Every season starts here.</h2><p>Revisit the opening order and the picks that built each franchise’s roster.</p><a class="button button--gold" href="{{ '/drafts/' | relative_url }}">Draft archive →</a></div>
  <div id="draft-countdown" data-season="{{ site.data.site.current_season }}" data-datetime="{{ site.data.league.draft_datetime }}" data-complete-message="The scheduled draft time has passed. Visit Yahoo for the latest results."><p class="eyebrow">{{ site.data.site.current_season }} draft</p><strong data-countdown-status>{% if site.data.league.draft_datetime %}{{ site.data.league.draft_datetime | date: '%B %-d, %Y' }}{% else %}Date to be announced{% endif %}</strong>{% if latest_draft %}<a class="text-link" href="{{ '/drafts/' | append: latest_draft.year | append: '/' | relative_url }}">Latest archived draft · {{ latest_draft.year }} →</a>{% endif %}</div>
</div></section>

<section class="content-section content-section--neutral" aria-labelledby="home-community-heading"><div class="wrap">
  {% include section-heading.html id="home-community-heading" eyebrow="The league conversation" title="Have Your Say" href="/votes/" link_text="Community" %}
  <div class="community-desk"><article><h3>Power Rankings</h3>{% include live-power-preview.html power=live.power_rankings %}</article><article><h3>Pick’em</h3>{% include pickem-preview.html picks=live.picks %}</article><article><h3>League Votes</h3>{% if live.active_vote %}<p>{{ live.active_vote.title }}</p>{% else %}<p>Proposals, awards, and league decisions. New ballots appear here when voting opens.</p>{% endif %}<a class="text-link" href="{{ '/votes/' | relative_url }}">League ballots →</a></article></div>
</div></section>
