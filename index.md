---
layout: default
title: Home
---

<section class="hero">
  <h1>Road to Glory FFL</h1>
  <p>Live league hub. Data updates automatically from Yahoo.</p>
</section>

<div class="grid">

  <!-- STANDINGS -->
  <div class="card">
    <h2>Standings</h2>
    {% if site.data.standings_simple %}
    <table class="table">
      <thead>
        <tr><th>#</th><th>Team</th><th>W</th><th>L</th><th>T</th><th>PF</th><th>PA</th></tr>
      </thead>
      <tbody>
        {% for t in site.data.standings_simple %}
        <tr>
          <td>{{ forloop.index }}</td>
          <td>{{ t.team }}</td>
          <td>{{ t.wins }}</td>
          <td>{{ t.losses }}</td>
          <td>{{ t.ties }}</td>
          <td>{{ t.points_for }}</td>
          <td>{{ t.points_against }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
      <p><em>Waiting for _data/standings_simple.json…</em></p>
    {% endif %}
  </div>

  <!-- MATCHUPS + EXPANDABLE ROSTERS -->
  <div class="card">
    <h2>This Week’s Matchups</h2>
    {% assign sb = site.data.scoreboard_simple %}
    {% assign ro = site.data.rosters_simple %}
    {% if sb and sb.matchups and sb.matchups.size > 0 %}
      <p>Week {{ sb.week | default: '?' }}</p>
      <ul>
      {% for m in sb.matchups %}
        <li style="margin-bottom:10px;">
          <strong>{{ m.team_a }}</strong> ({{ m.points_a | default: 0 }})
          &nbsp;vs&nbsp;
          <strong>{{ m.team_b }}</strong> ({{ m.points_b | default: 0 }})

          <!-- Team A roster -->
          {% assign teamA = m.team_a %}
          {% assign rosterA = nil %}
          {% for t in ro.teams %}
            {% if t.team == teamA %}
              {% assign rosterA = t %}
              {% break %}
            {% endif %}
          {% endfor %}
          {% if rosterA %}
          <details style="margin-top:6px;">
            <summary>Show {{ teamA }} roster</summary>
            <ul>
              {% for p in rosterA.players %}
                <li>{{ p.position | default: "—" }} — {{ p.name }}</li>
              {% endfor %}
            </ul>
          </details>
          {% endif %}

          <!-- Team B roster -->
          {% assign teamB = m.team_b %}
          {% assign rosterB = nil %}
          {% for t in ro.teams %}
            {% if t.team == teamB %}
              {% assign rosterB = t %}
              {% break %}
            {% endif %}
          {% endfor %}
          {% if rosterB %}
          <details style="margin-top:6px;">
            <summary>Show {{ teamB }} roster</summary>
            <ul>
              {% for p in rosterB.players %}
                <li>{{ p.position | default: "—" }} — {{ p.name }}</li>
              {% endfor %}
            </ul>
          </details>
          {% endif %}
        </li>
      {% endfor %}
      </ul>
    {% else %}
      <p><em>Waiting for _data/scoreboard_simple.json and _data/rosters_simple.json…</em></p>
    {% endif %}
  </div>

  <!-- DEBUG / META (optional; remove later) -->
  <div class="card">
    <h2>League Meta</h2>
    <pre>{{ site.data.league_meta | jsonify | escape }}</pre>
  </div>

</div>
