---
layout: default
title: League Votes
permalink: /votes/
description: Road to Glory FFL polls, manager-voted Power Rankings, weekly matchup picks, and season Picks Leaderboard.
---

{% assign public_votes = site.data.generated.votes %}
{% assign power = site.data.generated.power_rankings %}
{% assign picks = site.data.generated.picks %}

<section class="vote-hero">
  <div class="wrap vote-hero__grid">
    <div><p class="eyebrow">The league conversation</p><h1>League<br>Votes</h1><p>Manager ballots, weekly predictions, and the public results that turn twelve opinions into one league conversation.</p><div class="vote-hero__actions"><a class="button button--gold" href="#active-votes">See active votes</a><a class="text-link" href="{{ '/power-rankings/' | relative_url }}">Power Rankings <span aria-hidden="true">→</span></a></div></div>
    <aside class="vote-principles"><span>Three ways to have your say</span><strong>Rank the league.<br>Call the winners.</strong><ul><li>Power Rankings · your weekly top twelve</li><li>Pick’em · every matchup, every week</li><li>League Votes · proposals and awards</li></ul></aside>
  </div>
</section>

<nav class="vote-jump" aria-label="League Votes sections"><div class="wrap"><a href="#active-votes">Active votes</a><a href="#weekly-picks">Matchup picks</a><a href="#power-rankings">Power Rankings</a><a href="#vote-archive">Archive</a></div></nav>

<section class="shell-content vote-section" id="active-votes" aria-labelledby="active-votes-heading">
  <div class="section-heading"><div><p class="eyebrow">Your voice, on the record</p><h2 id="active-votes-heading">Active Votes</h2><p>Rule proposals, awards, and other commissioner-approved ballots appear here when voting opens.</p></div><span class="vote-status-badge">{{ public_votes.active_polls.size }} open</span></div>
  {% if public_votes.active_polls.size > 0 %}
    <div class="poll-grid">
      {% for poll in public_votes.active_polls %}<article class="poll-card"><div class="poll-card__meta"><span>{{ poll.type | replace: '_', ' ' }}</span>{% if poll.close_date %}<time datetime="{{ poll.close_date }}">Closes {{ poll.close_date | date: '%b %-d, %-I:%M %p' }}</time>{% endif %}</div><h3>{{ poll.title }}</h3><p>{{ poll.description }}</p>{% if poll.results.size > 0 %}<div class="poll-results">{% for option in poll.results %}<div><span><strong>{{ option.label }}</strong><small>{{ option.vote_count }} votes · {{ option.percentage | times: 100 | round: 1 }}%</small></span><i style="--result: {{ option.percentage | times: 100 }}%"></i></div>{% endfor %}</div>{% endif %}{% if poll.embed_url %}<iframe class="poll-embed" src="{{ poll.embed_url }}" title="{{ poll.title }} ballot" loading="lazy" sandbox="allow-forms allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe>{% endif %}{% if poll.form_url %}<a class="button button--gold" href="{{ poll.form_url }}" target="_blank" rel="noopener noreferrer">Open ballot <span aria-hidden="true">↗</span></a>{% endif %}</article>{% endfor %}
    </div>
  {% else %}
    <div class="vote-empty"><span aria-hidden="true">0</span><div><h3>No league ballots are open</h3><p>The next commissioner-approved proposal or award vote will appear here with its real deadline and public ballot link.</p></div></div>
  {% endif %}
</section>

{% if public_votes.upcoming_polls.size > 0 %}<section class="shell-content vote-section" aria-labelledby="upcoming-votes-heading"><div class="section-heading"><div><p class="eyebrow">On deck</p><h2 id="upcoming-votes-heading">Upcoming Votes</h2></div></div><div class="poll-grid">{% for poll in public_votes.upcoming_polls %}<article class="poll-card"><div class="poll-card__meta"><span>{{ poll.type | replace: '_', ' ' }}</span>{% if poll.open_date %}<time datetime="{{ poll.open_date }}">Opens {{ poll.open_date | date: '%b %-d' }}</time>{% endif %}</div><h3>{{ poll.title }}</h3><p>{{ poll.description }}</p></article>{% endfor %}</div></section>{% endif %}

<section class="content-section content-section--navy vote-section" id="weekly-picks" aria-labelledby="weekly-picks-heading"><div class="wrap">
  <div class="section-heading section-heading--light"><div><p class="eyebrow">Call the winners</p><h2 id="weekly-picks-heading">Weekly Matchup Picks</h2><p>Pick each winner before the commissioner closes the weekly form. Final scoring waits for a verified Yahoo result.</p></div><a class="button button--outline-light" href="{{ '/picks/' | relative_url }}">Picks center</a></div>
  {% if picks.current_week %}
    <div class="vote-matchup-grid">{% for matchup in picks.current_week.matchups %}<article class="vote-matchup-card"><span>Week {{ matchup.week }}</span><div>{% for team in matchup.participants %}<a href="{{ team.path | relative_url }}"><img src="{{ team.identity_image | relative_url }}" alt=""><strong>{{ team.display_name }}</strong></a>{% unless forloop.last %}<b>VS</b>{% endunless %}{% endfor %}</div><small>{% if matchup.winner_status == 'verified' %}Final winner verified{% elsif picks.current_week.state == 'open' %}Voting window open in Google Forms{% elsif picks.current_week.state == 'locked' %}Picks locked{% else %}Pick’em opens soon{% endif %}</small></article>{% endfor %}</div>
  {% else %}
    <div class="vote-empty vote-empty--dark"><span aria-hidden="true">W</span><div><h3>Weekly matchup voting opens with the season</h3><p>The committed Yahoo snapshot is not yet the current 2026 schedule, so no stale or fabricated matchups are offered.</p></div></div>
  {% endif %}
</div></section>

<section class="shell-content vote-section" id="power-rankings" aria-labelledby="power-heading">
  <div class="community-feature-grid">
    <article class="community-feature"><p class="eyebrow">Managers rank all twelve</p><h2 id="power-heading">Power Rankings</h2>{% if power.rankings.size > 0 %}<ol class="power-preview">{% for team in power.rankings limit: 5 %}<li><span>{{ team.rank }}</span><img src="{{ team.identity_image | relative_url }}" alt=""><a href="{{ team.path | relative_url }}">{{ team.display_name }}</a><strong>{{ team.average_rank }}</strong></li>{% endfor %}</ol>{% else %}<div class="feature-empty"><strong>Voting opens during the season.</strong><p>These rankings will come entirely from manager ballots—not Yahoo standings or an algorithm.</p></div>{% endif %}<a class="text-link" href="{{ '/power-rankings/' | relative_url }}">Open Power Rankings <span aria-hidden="true">→</span></a></article>
    <article class="community-feature community-feature--gold"><p class="eyebrow">Season-long prediction race</p><h2>Picks Leaderboard</h2>{% if picks.leaderboard.size > 0 %}<ol class="picks-preview">{% for manager in picks.leaderboard limit: 5 %}<li><span>{{ manager.rank }}</span><strong>{{ manager.display_name }}</strong><b>{{ manager.correct }}</b><small>{{ manager.accuracy | times: 100 | round: 1 }}%</small></li>{% endfor %}</ol>{% else %}<div class="feature-empty"><strong>Results begin after verified games.</strong><p>Correct picks earn one point. Pending matchups and missing winners never count as losses.</p></div>{% endif %}<a class="text-link" href="{{ '/picks/' | relative_url }}">Open Picks Leaderboard <span aria-hidden="true">→</span></a></article>
  </div>
</section>

<section class="content-section vote-section vote-archive" id="vote-archive" aria-labelledby="vote-archive-heading"><div class="wrap">
  <div class="section-heading"><div><p class="eyebrow">Closed and counted</p><h2 id="vote-archive-heading">Vote Archive</h2><p>Final general-vote results remain available without exposing individual voter identity or private response metadata.</p></div></div>
  {% if public_votes.archived_polls.size > 0 %}<div class="poll-grid">{% for poll in public_votes.archived_polls %}<article class="poll-card"><div class="poll-card__meta"><span>{{ poll.season }}</span><span>{{ poll.ballots_counted }} ballots</span></div><h3>{{ poll.title }}</h3><p>{{ poll.description }}</p>{% if poll.result_summary %}<p><strong>{{ poll.result_summary }}</strong></p>{% endif %}{% if poll.results.size > 0 %}<div class="poll-results">{% for option in poll.results %}<div><span><strong>{{ option.label }}</strong><small>{{ option.vote_count }} votes · {{ option.percentage | times: 100 | round: 1 }}%</small></span><i style="--result: {{ option.percentage | times: 100 }}%"></i></div>{% endfor %}</div>{% endif %}</article>{% endfor %}</div>{% else %}<div class="vote-empty"><span aria-hidden="true">—</span><div><h3>No completed votes yet</h3><p>Only real commissioner-approved results will enter this archive.</p></div></div>{% endif %}
</div></section>
