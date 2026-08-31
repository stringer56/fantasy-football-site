---
layout: default
title: Home
---

<section class="hero">
  <h1>Road to Glory FFL</h1>
  <p>Live league hub. Data updates automatically from Yahoo.</p>
</section>

## League News
<div class="card ticker-wrap">
  {% if site.data.news and site.data.news.items and site.data.news.items.size > 0 %}
    <div class="ticker">
      {% for item in site.data.news.items %}
        <span><span class="src">{{ item.source }}</span><a href="{{ item.link }}" target="_blank" rel="noopener">{{ item.title }}</a></span>
      {% endfor %}
      {% for item in site.data.news.items %}
        <span><span class="src">{{ item.source }}</span><a href="{{ item.link }}" target="_blank" rel="noopener">{{ item.title }}</a></span>
      {% endfor %}
    </div>
  {% else %}
    <div style="padding:10px;">League news is being updated.</div>
  {% endif %}
</div>

{% assign generated = site.data.generated %}
{% assign current_season = site.data.site.current_season %}
{% assign generated_season = generated.manifest.season %}
{% assign data_is_current = false %}
{% if generated_season == current_season %}
  {% assign data_is_current = true %}
{% endif %}
{% assign standings_data = generated.standings %}
{% assign matchups_data = generated.matchups %}
{% assign rosters_data = generated.rosters %}

<div class="grid">
  <div class="card">
    <h2>Standings</h2>
    {% if data_is_current and standings_data and standings_data.standings and standings_data.standings.size > 0 %}
    <table class="table">
      <thead><tr><th>#</th><th>Team</th><th>W</th><th>L</th><th>T</th><th>PF</th><th>PA</th></tr></thead>
      <tbody>
        {% for team in standings_data.standings %}
        <tr>
          <td>{{ team.rank | default: forloop.index }}</td>
          <td>{{ team.team_name }}</td>
          <td>{{ team.wins }}</td>
          <td>{{ team.losses }}</td>
          <td>{{ team.ties }}</td>
          <td>{{ team.points_for | round: 2 }}</td>
          <td>{{ team.points_against | round: 2 }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
      <p><em>League data is being updated.</em></p>
    {% endif %}
  </div>

  <div class="card">
    <h2>This Week’s Matchups</h2>
    {% if data_is_current and matchups_data and matchups_data.matchups and matchups_data.matchups.size > 0 %}
      <p>Week {{ matchups_data.week | default: '?' }}</p>
      <ul>
      {% for matchup in matchups_data.matchups %}
        {% assign team_a = matchup.teams[0] %}
        {% assign team_b = matchup.teams[1] %}
        <li style="margin-bottom:10px;">
          <strong>{{ team_a.team_name }}</strong> ({{ team_a.score | default: '—' }})
          &nbsp;vs&nbsp;
          <strong>{{ team_b.team_name }}</strong> ({{ team_b.score | default: '—' }})

          {% if rosters_data and rosters_data.teams %}
            {% assign roster_a = rosters_data.teams | where: 'team_key', team_a.team_key | first %}
            {% if roster_a and roster_a.players and roster_a.players.size > 0 %}
            <details style="margin-top:6px;">
              <summary>Show {{ team_a.team_name }} roster</summary>
              <ul>
                {% for player in roster_a.players %}
                  <li>{{ player.selected_position | default: player.primary_position | default: "—" }} — {{ player.player_name }}</li>
                {% endfor %}
              </ul>
            </details>
            {% endif %}

            {% assign roster_b = rosters_data.teams | where: 'team_key', team_b.team_key | first %}
            {% if roster_b and roster_b.players and roster_b.players.size > 0 %}
            <details style="margin-top:6px;">
              <summary>Show {{ team_b.team_name }} roster</summary>
              <ul>
                {% for player in roster_b.players %}
                  <li>{{ player.selected_position | default: player.primary_position | default: "—" }} — {{ player.player_name }}</li>
                {% endfor %}
              </ul>
            </details>
            {% endif %}
          {% endif %}
        </li>
      {% endfor %}
      </ul>
    {% else %}
      <p><em>League data is being updated.</em></p>
    {% endif %}
  </div>
</div>
