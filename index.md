# Road to Glory Fantasy Football League

Welcome to the official league site for Road to Glory FFL! Data below is automatically pulled from Yahoo and refreshed regularly.

---

## Standings
<div class="card">
  <h2>Standings</h2>
  {% if site.data.standings_simple %}
  <table class="table">
    <thead>
      <tr>
        <th>#</th>
        <th>Team</th>
        <th>W</th>
        <th>L</th>
        <th>T</th>
        <th>PF</th>
        <th>PA</th>
      </tr>
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

---

## This Week’s Matchups
<div class="card">
  <h2>This Week’s Matchups</h2>
  {% if site.data.scoreboard_simple and site.data.scoreboard_simple.size > 0 %}
    <ul>
      {% for m in site.data.scoreboard_simple %}
        <li>
          <strong>{{ m.team_a }}</strong> ({{ m.points_a | default: 0 }})
          vs
          <strong>{{ m.team_b }}</strong> ({{ m.points_b | default: 0 }})
        </li>
      {% endfor %}
    </ul>
  {% else %}
    <p><em>Waiting for _data/scoreboard_simple.json…</em></p>
  {% endif %}
</div>

---

## League Information
<div class="card">
  <h2>League Meta</h2>
  <pre>{{ site.data.league_meta | jsonify | escape }}</pre>
</div>
