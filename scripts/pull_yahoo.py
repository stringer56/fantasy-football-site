import os, json, base64, pathlib, requests

API = "https://fantasysports.yahooapis.com/fantasy/v2"

def refresh_access_token(client_id, client_secret, refresh_token):
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type":"refresh_token","refresh_token":refresh_token}
    r = requests.post("https://api.login.yahoo.com/oauth2/get_token", headers=headers, data=data, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def get_json(url, token):
    headers = {"Authorization": f"Bearer {token}", "Accept":"application/json"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    if "application/json" in r.headers.get("Content-Type",""): return r.json()
    return {"raw": r.text}

def write_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("wrote", path)

# ---- small JSON helpers (tolerant to Yahoo nesting) ----
def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values(): yield from walk(v)
    elif isinstance(obj, list):
        for v in obj: yield from walk(v)

def find_all(obj, key):
    for d in walk(obj):
        if key in d: yield d[key]

def flatten_team(node):
    """Yahoo returns team as a list of dicts; flatten to one dict with name, team_key, etc."""
    if isinstance(node, dict):
        return node
    if isinstance(node, list):
        out = {}
        for part in node:
            if isinstance(part, dict): out.update(part)
        return out
    return {}

def normalize_standings(data):
    teams = []
    for node in find_all(data, "team"):
        base = flatten_team(node)
        name = base.get("name") or base.get("nickname")
        ts = base.get("team_standings") or {}
        outcomes = ts.get("outcome_totals") or {}
        pf = ts.get("points_for") or ts.get("points_for_total") or base.get("points_for")
        pa = ts.get("points_against") or ts.get("points_against_total") or base.get("points_against")
        if name:
            teams.append({
                "team": name,
                "wins": int(outcomes.get("wins") or 0),
                "losses": int(outcomes.get("losses") or 0),
                "ties": int(outcomes.get("ties") or 0),
                "points_for": float(pf) if pf is not None else None,
                "points_against": float(pa) if pa is not None else None
            })
    teams.sort(key=lambda x: (x["wins"], x.get("points_for") or 0.0), reverse=True)
    return teams

def normalize_scoreboard(data):
    matchups = []
    # try to capture current scoring week
    current_week = None
    for d in walk(data):
        if isinstance(d, dict) and "week" in d and isinstance(d["week"], str):
            current_week = d["week"]
            break

    for mnode in find_all(data, "matchup"):
        base = mnode if isinstance(mnode, dict) else flatten_team(mnode)  # not really a team, just reuse
        teams_block = base.get("teams") or {}
        titems = []
        if isinstance(teams_block, dict):
            for k,v in teams_block.items():
                if k == "count": continue
                if isinstance(v, dict) and "team" in v:
                    titems.append(v["team"])
        def extract(t):
            info = flatten_team(t)
            name = info.get("name")
            pts = None
            if "team_points" in info and isinstance(info["team_points"], dict):
                val = info["team_points"].get("total") or info["team_points"].get("value")
                try: pts = float(val)
                except: pts = None
            return name, pts
        if len(titems) == 2:
            a_name, a_pts = extract(titems[0])
            b_name, b_pts = extract(titems[1])
            matchups.append({
                "team_a": a_name, "points_a": a_pts,
                "team_b": b_name, "points_b": b_pts
            })
    return {"week": current_week, "matchups": matchups}

def build_teamkey_map(teams_json):
    """Return {team_name: team_key} using the /teams endpoint."""
    mapping = {}
    for tnode in find_all(teams_json, "team"):
        base = flatten_team(tnode)
        name = base.get("name") or base.get("nickname")
        tkey = base.get("team_key")
        if name and tkey:
            mapping[name] = tkey
    return mapping

def fetch_roster_simple(team_key, token, week=None):
    url = f"{API}/team/{team_key}/roster?format=json"
    if week: url += f"&week={week}"
    js = get_json(url, token)
    players = []
    for pnode in find_all(js, "player"):
        # flatten
        base = {}
        if isinstance(pnode, list):
            for part in pnode:
                if isinstance(part, dict): base.update(part)
        elif isinstance(pnode, dict):
            base = pnode
        # name
        pname = None
        for nm in find_all(base, "full"):
            pname = nm; break
        # position (selected_position > position)
        pos = None
        if "selected_position" in base and isinstance(base["selected_position"], dict):
            pos = base["selected_position"].get("position")
        if not pos and "primary_position" in base:
            pos = base.get("primary_position")
        players.append({"name": pname, "position": pos})
    return players

def main():
    cid = os.environ["YAHOO_CLIENT_ID"]
    csec = os.environ["YAHOO_CLIENT_SECRET"]
    rtok = os.environ["YAHOO_REFRESH_TOKEN"]
    league = os.environ["LEAGUE_KEY"]  # e.g., nfl.l.103926

    token = refresh_access_token(cid, csec, rtok)

    outdir = pathlib.Path("_data"); outdir.mkdir(exist_ok=True)

    league_meta = get_json(f"{API}/league/{league}?format=json", token)
    standings   = get_json(f"{API}/league/{league}/standings?format=json", token)
    scoreboard  = get_json(f"{API}/league/{league}/scoreboard?format=json", token)
    teams       = get_json(f"{API}/league/{league}/teams?format=json", token)

    # write raw
    write_json(outdir/"league_meta.json", league_meta)
    write_json(outdir/"standings.json", standings)
    write_json(outdir/"scoreboard.json", scoreboard)
    write_json(outdir/"teams.json", teams)

    # simplified
    standings_simple  = normalize_standings(standings)
    scoreboard_simpl  = normalize_scoreboard(scoreboard)
    write_json(outdir/"standings_simple.json", standings_simple)
    write_json(outdir/"scoreboard_simple.json", scoreboard_simpl)

    # rosters for current week matchups
    teamkey_by_name = build_teamkey_map(teams)
    week = scoreboard_simpl.get("week")
    rosters_simple = {"week": week, "teams": []}
    seen = set()
    for m in scoreboard_simpl.get("matchups", []):
        for name in (m.get("team_a"), m.get("team_b")):
            if not name or name in seen: continue
            tkey = teamkey_by_name.get(name)
            if not tkey: continue
            players = fetch_roster_simple(tkey, token, week=week)
            rosters_simple["teams"].append({"team": name, "players": players})
            seen.add(name)
    write_json(outdir/"rosters_simple.json", rosters_simple)

if __name__ == "__main__":
    main()
