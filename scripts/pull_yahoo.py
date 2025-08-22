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

# ---- Helpers to safely pull values from Yahoo's nested JSON ----
def rget(d, *keys):
    cur = d
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return None
    return cur

def walk(obj):
    """Yield every dict you can find (depth-first)."""
    if isinstance(obj, dict):
        yield obj
        for v in obj.values(): yield from walk(v)
    elif isinstance(obj, list):
        for v in obj: yield from walk(v)

def find_all(obj, key):
    for d in walk(obj):
        if key in d: yield d[key]

# ---- Normalizers (tolerant of Yahoo's arrays/lists) ----
def normalize_standings(data):
    teams = []
    for node in find_all(data, "team"):
        # node is usually a list with one dict containing 'name', 'team_standings', etc.
        if isinstance(node, list):
            base = {}
            for part in node:
                if isinstance(part, dict):
                    base.update(part)
            name = base.get("name") or base.get("nickname")
            ts = base.get("team_standings") or {}
            outcomes = rget(ts, "outcome_totals") or {}
            pf = ts.get("points_for") or ts.get("points_for_total") or base.get("points_for")
            pa = ts.get("points_against") or ts.get("points_against_total") or base.get("points_against")
            try_pf = float(pf) if pf is not None else None
            try_pa = float(pa) if pa is not None else None
            wins = outcomes.get("wins") or outcomes.get("wins_total")
            losses = outcomes.get("losses") or outcomes.get("losses_total")
            ties = outcomes.get("ties") or "0"
            if name:
                teams.append({
                    "team": name,
                    "wins": int(wins) if wins is not None else None,
                    "losses": int(losses) if losses is not None else None,
                    "ties": int(ties) if ties is not None else 0,
                    "points_for": try_pf,
                    "points_against": try_pa
                })
    # sort by wins desc, then PF desc
    teams = [t for t in teams if t.get("wins") is not None]
    teams.sort(key=lambda x: (x["wins"], x.get("points_for") or 0), reverse=True)
    return teams

def normalize_scoreboard(data):
    """Return a flat list of matchups with team names and points."""
    matchups = []
    # Yahoo wraps matchups under 'matchups'-> {count, 0:{matchup:{...}}, 1:{matchup:{...}}}
    for mnode in find_all(data, "matchup"):
        if isinstance(mnode, list):
            base = {}
            for part in mnode:
                if isinstance(part, dict): base.update(part)
        elif isinstance(mnode, dict):
            base = mnode
        else:
            continue

        # teams are usually under 'teams' keyed numerically
        teams_block = base.get("teams") or {}
        titems = []
        if isinstance(teams_block, dict):
            for k,v in teams_block.items():
                if k == "count": continue
                if isinstance(v, dict) and "team" in v:
                    titems.append(v["team"])
        # each team entry is a list; pull 'name' and 'team_points'
        row = {"status": base.get("status") or base.get("is_playoffs") or ""}
        if len(titems) == 2:
            def extract(t):
                info = {}
                if isinstance(t, list):
                    for part in t:
                        if isinstance(part, dict): info.update(part)
                name = info.get("name")
                pts = None
                if "team_points" in info and isinstance(info["team_points"], dict):
                    val = info["team_points"].get("total") or info["team_points"].get("value")
                    try:
                        pts = float(val)
                    except:
                        pts = None
                return name, pts
            a_name, a_pts = extract(titems[0])
            b_name, b_pts = extract(titems[1])
            row.update({"team_a": a_name, "points_a": a_pts, "team_b": b_name, "points_b": b_pts})
            matchups.append(row)
    return matchups

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

    write_json(outdir/"league_meta.json", league_meta)
    write_json(outdir/"standings.json", standings)
    write_json(outdir/"scoreboard.json", scoreboard)
    write_json(outdir/"teams.json", teams)

    # NEW: simplified files
    write_json(outdir/"standings_simple.json", normalize_standings(standings))
    write_json(outdir/"scoreboard_simple.json", normalize_scoreboard(scoreboard))

if __name__ == "__main__":
    main()
