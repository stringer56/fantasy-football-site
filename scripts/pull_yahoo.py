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
    if "application/json" in r.headers.get("Content-Type",""):
        return r.json()
    return {"raw": r.text}

def write_data(name, data, outdir):
    p = pathlib.Path(outdir); p.mkdir(exist_ok=True)
    (p/f"{name}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("wrote", p/f"{name}.json")

def main():
    cid = os.environ["YAHOO_CLIENT_ID"]
    csec = os.environ["YAHOO_CLIENT_SECRET"]
    rtok = os.environ["YAHOO_REFRESH_TOKEN"]
    league = os.environ["LEAGUE_KEY"]  # e.g., nfl.l.12345
    token = refresh_access_token(cid, csec, rtok)
    write_data("league_meta", get_json(f"{API}/league/{league}?format=json", token), "_data")
    write_data("standings",   get_json(f"{API}/league/{league}/standings?format=json", token), "_data")
    write_data("scoreboard",  get_json(f"{API}/league/{league}/scoreboard?format=json", token), "_data")
    write_data("teams",       get_json(f"{API}/league/{league}/teams?format=json", token), "_data")

if __name__ == "__main__":
    main()
