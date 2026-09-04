"""Public Yahoo league-page fallback for sanitized current-season data.

The documented Fantasy API remains the primary source. This module is used only
when that authenticated request is unavailable; it reads the same official
Yahoo league pages already used by the historical backfill and emits the
existing public schema rather than exposing raw HTML to templates.
"""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
from datetime import datetime, timezone
from typing import Any

import yaml

try:
    from .yahoo_archive import ArchiveClient, clean_text, parse_available_weeks, parse_roster
except ImportError:
    from yahoo_archive import ArchiveClient, clean_text, parse_available_weeks, parse_roster


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = ROOT / "_data" / "generated"
HISTORY_MANIFEST = OUTPUT_DIRECTORY / "history_manifest.json"
SITE_CONFIG = ROOT / "_data" / "site.yml"
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
TEAM_HREF = re.compile(r"/f1/\d+/(?P<team>\d+)(?:[/?\"']|$)")


def _float(value: str) -> float | None:
    match = NUMBER.search(clean_text(value).replace(",", ""))
    return round(float(match.group()), 2) if match else None


def _attrs(fragment: str) -> dict[str, str]:
    return {
        key.casefold(): html.unescape(value)
        for key, _, value in re.findall(
            r"([:\w-]+)\s*=\s*(['\"])(.*?)\2", fragment, re.S
        )
    }


def _team_key(game_key: str, league_id: str, team_id: int) -> str:
    return f"{game_key}.l.{league_id}.t.{team_id}"


def parse_current_week(page: str) -> int | None:
    selected = re.search(
        r"<option[^>]+value=['\"][^'\"]*matchup_week=(\d+)[^'\"]*['\"][^>]*selected",
        page,
        re.I,
    )
    if selected:
        return int(selected.group(1))
    heading = re.search(r"Week\s+(\d+)\s+Matchups", page, re.I)
    return int(heading.group(1)) if heading else None


def parse_live_standings(
    page: str, *, game_key: str, league_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    table = re.search(
        r"<table\b[^>]*id=['\"]standingstable['\"][^>]*>(.*?)</table>",
        page,
        re.I | re.S,
    )
    if not table:
        raise ValueError("standings table not found")

    standings: list[dict[str, Any]] = []
    teams: list[dict[str, Any]] = []
    for row_tag, body in re.findall(
        r"<tr\b([^>]*)>(.*?)</tr>", table.group(1), re.I | re.S
    ):
        target = _attrs(row_tag).get("data-target", "")
        team_match = TEAM_HREF.search(target)
        cells = re.findall(r"<td\b[^>]*>(.*?)</td>", body, re.I | re.S)
        if not team_match or len(cells) < 5:
            continue

        team_cell = cells[1]
        anchors = re.findall(r"<a\b([^>]*)>(.*?)</a>", team_cell, re.I | re.S)
        team_name = next(
            (clean_text(content) for _, content in anchors if clean_text(content)), ""
        ).replace("\ufffd", "’")
        wlt = re.fullmatch(r"(\d+)-(\d+)-(\d+)", clean_text(cells[2]))
        if not team_name or not wlt:
            continue

        team_id = int(team_match.group("team"))
        key = _team_key(game_key, league_id, team_id)
        wins, losses, ties = (int(wlt.group(1)), int(wlt.group(2)), int(wlt.group(3)))
        games = wins + losses + ties
        rank_match = re.search(r"\d+", clean_text(cells[0]))
        streak_text = clean_text(cells[5]) if len(cells) > 5 else ""
        streak_match = re.fullmatch(r"([WL])[- ]?(\d+)", streak_text, re.I)
        logo_match = re.search(r"<img\b[^>]*src=['\"]([^'\"]+)", team_cell, re.I)
        waiver = _float(cells[6]) if len(cells) > 6 else None
        moves = _float(cells[7]) if len(cells) > 7 else None

        teams.append(
            {
                "team_key": key,
                "team_id": team_id,
                "team_name": team_name,
                "managers": [],
                "team_logo_url": html.unescape(logo_match.group(1)) if logo_match else None,
                "waiver_priority": int(waiver) if waiver is not None else None,
                "number_of_moves": int(moves) if moves is not None else None,
                "number_of_trades": None,
            }
        )
        standings.append(
            {
                "rank": int(rank_match.group()) if rank_match else None,
                "team_key": key,
                "team_id": team_id,
                "team_name": team_name,
                "wins": wins,
                "losses": losses,
                "ties": ties,
                "winning_percentage": round((wins + ties * 0.5) / games, 6) if games else None,
                "points_for": _float(cells[3]),
                "points_against": _float(cells[4]),
                "streak": (
                    {"type": "win" if streak_match.group(1).upper() == "W" else "loss", "value": int(streak_match.group(2))}
                    if streak_match
                    else None
                ),
                "playoff_seed": None,
            }
        )

    if not teams:
        raise ValueError("standings table contained no valid teams")
    standings.sort(
        key=lambda row: (
            row["rank"] is None,
            row["rank"] if row["rank"] is not None else row["team_id"],
        )
    )
    teams.sort(key=lambda row: row["team_id"])
    return standings, teams


def parse_live_matchups(
    page: str, *, week: int, game_key: str, league_id: str
) -> list[dict[str, Any]]:
    start = re.search(r"<section\b[^>]*id=['\"]matchupweek['\"][^>]*>", page, re.I)
    if not start:
        raise ValueError("matchup section not found")
    fragment = page[start.start() :]
    end = re.search(r"<section\b[^>]*id=['\"]scoreboard['\"]", fragment, re.I)
    if end:
        fragment = fragment[: end.start()]

    header = clean_text(fragment[:3000]).casefold()
    if "final results" in header:
        status = "postevent"
    elif "not started" in header or "upcoming" in header:
        status = "preevent"
    else:
        status = "midevent"

    rows: list[dict[str, Any]] = []
    row_pattern = re.compile(
        r"<li\b([^>]*data-target\s*=\s*(['\"])[^'\"]*matchup\?[^'\"]*\2[^>]*)>(.*?)</li>",
        re.I | re.S,
    )
    for row_tag, _, body in row_pattern.findall(fragment):
        target = _attrs(row_tag).get("data-target", "")
        ids = re.search(r"mid1=(\d+).*?mid2=(\d+)", html.unescape(target))
        anchors: list[tuple[int, str]] = []
        for attrs_raw, content in re.findall(r"<a\b([^>]*)>(.*?)</a>", body, re.I | re.S):
            attrs = _attrs(attrs_raw)
            href_match = TEAM_HREF.search(attrs.get("href", ""))
            name = clean_text(content).replace("\ufffd", "’")
            if "F-link" in attrs.get("class", "").split() and href_match and name:
                anchors.append((int(href_match.group("team")), name))

        score_pairs = re.findall(
            r"<div\b[^>]*class\s*=\s*(['\"])[^'\"]*\bFz-lg\b[^'\"]*\1[^>]*>(.*?)</div>\s*"
            r"<div\b[^>]*class\s*=\s*(['\"])[^'\"]*\bF-shade\b[^'\"]*\3[^>]*>(.*?)</div>",
            body,
            re.I | re.S,
        )
        if len(anchors) != 2 or len(score_pairs) < 2 or not ids:
            continue

        records = re.findall(r">\s*(\d+-\d+-\d+)\s*</div>", body, re.I)
        teams = []
        for index, (team_id, name) in enumerate(anchors[:2]):
            score = _float(score_pairs[index][1])
            projection = _float(score_pairs[index][3])
            teams.append(
                {
                    "team_key": _team_key(game_key, league_id, team_id),
                    "team_id": team_id,
                    "team_name": name,
                    "record": records[index] if index < len(records) else None,
                    "score": score,
                    "projected_score": projection,
                }
            )

        a_score, b_score = teams[0]["score"], teams[1]["score"]
        tied = status == "postevent" and a_score is not None and a_score == b_score
        winner_key = None
        if status == "postevent" and a_score is not None and b_score is not None and not tied:
            winner_key = teams[0]["team_key"] if a_score > b_score else teams[1]["team_key"]
        rows.append(
            {
                "week": week,
                "status": status,
                "is_playoffs": False,
                "is_consolation": False,
                "is_tied": tied,
                "winner_team_key": winner_key,
                "teams": teams,
            }
        )
    if not rows:
        raise ValueError(f"no valid matchups found for week {week}")
    return rows


def _write_json_if_changed(path: pathlib.Path, data: dict[str, Any]) -> bool:
    serialized = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == serialized:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8")
    temporary.replace(path)
    return True


def canonical_current_season_record(
    site_config: dict[str, Any], manifest: dict[str, Any]
) -> tuple[int, dict[str, Any]]:
    """Resolve the current Yahoo identity from reviewed human configuration."""
    current = int(site_config["current_season"])
    yahoo = site_config.get("yahoo") or {}
    required = ("season", "game_key", "league_id", "league_key", "alias", "league_url")
    missing = [field for field in required if yahoo.get(field) in (None, "")]
    if missing:
        raise ValueError(f"site Yahoo configuration is missing: {', '.join(missing)}")
    if int(yahoo["season"]) != current:
        raise ValueError("site current_season and yahoo.season must match")

    game_key = str(yahoo["game_key"])
    league_id = str(yahoo["league_id"])
    league_key = str(yahoo["league_key"])
    if league_key != f"{game_key}.l.{league_id}":
        raise ValueError("configured Yahoo league_key does not match game_key and league_id")
    if str(yahoo["alias"]) != f"nfl.l.{league_id}":
        raise ValueError("configured Yahoo alias does not match league_id")

    verified = next(
        (row for row in manifest.get("seasons", []) if row.get("season") == current),
        None,
    )
    if verified:
        for field in ("game_key", "league_id", "league_key"):
            if str(verified.get(field)) != str(yahoo[field]):
                raise ValueError(
                    f"configured Yahoo {field} conflicts with the verified history manifest"
                )

    return current, {
        "season": current,
        "game_key": game_key,
        "league_id": league_id,
        "league_key": league_key,
        "alias": str(yahoo["alias"]),
        "league_url": str(yahoo["league_url"]),
        "league_name": (verified or {}).get("league_name") or "Road To Glory FFL",
    }


def _current_season_record() -> tuple[int, dict[str, Any]]:
    site_config = yaml.safe_load(SITE_CONFIG.read_text(encoding="utf-8"))
    manifest = json.loads(HISTORY_MANIFEST.read_text(encoding="utf-8"))
    return canonical_current_season_record(site_config, manifest)


def build_public_page_payloads(
    page: str,
    *,
    season: int,
    game_key: str,
    league_id: str,
    league_name: str,
    generated_at: str,
    rosters: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    week = parse_current_week(page)
    if week is None:
        raise ValueError("current matchup week was not found")
    available_weeks = parse_available_weeks(page)
    standings, teams = parse_live_standings(page, game_key=game_key, league_id=league_id)
    matchups = parse_live_matchups(page, week=week, game_key=game_key, league_id=league_id)
    if len(teams) != 12:
        raise ValueError(f"expected 12 current teams, found {len(teams)}")
    if len(matchups) != 6:
        raise ValueError(f"expected 6 current matchups, found {len(matchups)}")
    return {
        "manifest.json": {
            "schema_version": 1,
            "season": season,
            "source_update_timestamp": generated_at,
            "status": "ready",
            "source": "official_yahoo_public_page_fallback",
        },
        "league.json": {
            "schema_version": 1,
            "league": {
                "league_key": f"{game_key}.l.{league_id}",
                "league_id": league_id,
                "league_name": league_name,
                "season": season,
                "number_of_teams": len(teams),
                "current_week": week,
                "matchup_week": week,
                "start_week": min(available_weeks) if available_weeks else None,
                "end_week": max(available_weeks) if available_weeks else None,
                "start_date": None,
                "end_date": None,
                "is_finished": False,
                "league_logo_url": None,
                "source_update_timestamp": generated_at,
            },
        },
        "teams.json": {"schema_version": 1, "teams": teams},
        "standings.json": {"schema_version": 1, "standings": standings},
        "matchups.json": {"schema_version": 1, "week": week, "matchups": matchups},
        "rosters.json": {"schema_version": 1, "week": week, "teams": rosters or []},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--skip-rosters", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    season, record = _current_season_record()
    game_key, league_id = str(record["game_key"]), str(record["league_id"])
    base_url = str(record["league_url"]).rstrip("/")
    client = ArchiveClient(ROOT / ".cache" / "yahoo-live", delay_seconds=args.delay)
    page = client.get(
        f"{base_url}?module=matchups&lhst=matchups",
        pathlib.Path(str(season)) / "current.html",
        refresh=args.refresh,
    )
    week = parse_current_week(page)
    if week is None:
        raise ValueError("current matchup week was not found")

    standings, teams = parse_live_standings(page, game_key=game_key, league_id=league_id)
    rosters: list[dict[str, Any]] = []
    if not args.skip_rosters:
        for team in teams:
            team_id = team["team_id"]
            try:
                team_page = client.get(
                    f"{base_url}/{team_id}/team?week={week}",
                    pathlib.Path(str(season)) / f"team-{team_id:02d}-week-{week:02d}.html",
                    refresh=args.refresh,
                )
                parsed = parse_roster(
                    team_page,
                    season=season,
                    week=week,
                    team_key=team["team_key"],
                    franchise_id=None,
                    historical_team_name=team["team_name"],
                )
            except (OSError, ValueError, RuntimeError):
                parsed = []
            rosters.append(
                {
                    "team_key": team["team_key"],
                    "team_id": team_id,
                    "team_name": team["team_name"],
                    "players": [
                        {
                            "player_key": f"{game_key}.p.{player['player_id']}" if player.get("player_id") else None,
                            "player_name": player.get("player_name"),
                            "nfl_team": None,
                            "primary_position": None,
                            "selected_position": player.get("selected_position"),
                            "status": None,
                        }
                        for player in parsed
                    ],
                }
            )

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    payloads = build_public_page_payloads(
        page,
        season=season,
        game_key=game_key,
        league_id=league_id,
        league_name=str(record.get("league_name") or "Road To Glory FFL"),
        generated_at=generated_at,
        rosters=rosters,
    )
    changed = sum(
        int(_write_json_if_changed(OUTPUT_DIRECTORY / name, payload))
        for name, payload in payloads.items()
    )
    print(
        f"Yahoo public fallback complete: {len(teams)} teams, "
        f"{len(standings)} standings rows, {len(payloads['matchups.json']['matchups'])} matchups, "
        f"{sum(len(row['players']) for row in rosters)} roster players, {changed} changed files"
    )


if __name__ == "__main__":
    main()
