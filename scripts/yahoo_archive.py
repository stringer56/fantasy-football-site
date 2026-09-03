"""Pure parsers and a rate-limited cache client for public Yahoo league archives."""

from __future__ import annotations

import html
import json
import pathlib
import random
import re
import time
from dataclasses import dataclass
from typing import Any, Callable

import requests


TEAM_HREF = re.compile(r"/(?:20\d{2}/)?f1/(?P<league>\d+)/(?P<team>\d+)(?:[/?'\"]|$)")
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def clean_text(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(value).replace("\u200b", " ").split())


def is_login_page(value: str) -> bool:
    return "<title>Login - Sign in to Yahoo</title>" in value or "Sign in to Yahoo Fantasy" in value


def _attrs(fragment: str) -> dict[str, str]:
    return {
        key.lower(): html.unescape(value)
        for key, _, value in re.findall(r"([\w:-]+)\s*=\s*(['\"])(.*?)\2", fragment, re.S)
    }


def _classes(fragment: str) -> set[str]:
    return set(_attrs(fragment).get("class", "").split())


def _float(value: str) -> float | None:
    match = NUMBER.search(clean_text(value).replace(",", ""))
    return float(match.group()) if match else None


def parse_available_weeks(page: str) -> list[int]:
    match = re.search(r"<section[^>]+id=['\"]matchupweek['\"].*?<select\b[^>]*>(.*?)</select>", page, re.I | re.S)
    if not match:
        return []
    return sorted({int(value) for value in re.findall(r"matchup_week=(\d+)", match.group(1))})


def parse_standings(page: str, *, season: int, game_key: str, league_id: str,
                    mappings: dict[str, str | None]) -> list[dict[str, Any]]:
    table = re.search(r"<table\b[^>]*id=['\"]standingstable['\"][^>]*>(.*?)</table>", page, re.I | re.S)
    if not table:
        raise ValueError("standings table not found")
    rows: list[dict[str, Any]] = []
    for row_tag, body in re.findall(r"<tr\b([^>]*)>(.*?)</tr>", table.group(1), re.I | re.S):
        target = _attrs(row_tag).get("data-target", "")
        team_match = TEAM_HREF.search(target)
        if not team_match:
            continue
        cells = re.findall(r"<td\b[^>]*>(.*?)</td>", body, re.I | re.S)
        if len(cells) < 5:
            continue
        anchors = re.findall(r"<a\b([^>]*)>(.*?)</a>", cells[1], re.I | re.S)
        team_name = next((clean_text(content) for attrs, content in anchors if clean_text(content)), "")
        rank_match = re.search(r"\d+", clean_text(cells[0]))
        wlt = re.fullmatch(r"(\d+)-(\d+)-(\d+)", clean_text(cells[2]))
        if not (team_name and rank_match and wlt):
            continue
        team_id = int(team_match.group("team"))
        team_key = f"{game_key}.l.{league_id}.t.{team_id}"
        wins, losses, ties = (int(wlt.group(1)), int(wlt.group(2)), int(wlt.group(3)))
        games = wins + losses + ties
        rank = int(rank_match.group())
        rows.append({
            "rank": rank,
            "yahoo_team_key": team_key,
            "yahoo_team_id": team_id,
            "franchise_id": mappings.get(team_key),
            "historical_team_name": team_name,
            "mapping_status": "verified" if mappings.get(team_key) else "unresolved",
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "win_percentage": round((wins + ties * 0.5) / games, 6) if games else None,
            "points_for": _float(cells[3]),
            "points_against": _float(cells[4]),
            "streak": clean_text(cells[5]) if len(cells) > 5 else None,
            "playoff_seed": rank if "*" in clean_text(cells[0]) else None,
            "playoff_finish": None,
        })
    if not rows:
        raise ValueError("standings table contained no valid rows")
    return rows


def parse_matchups(page: str, *, season: int, week: int, game_key: str,
                   league_id: str, mappings: dict[str, str | None],
                   playoff_start_week: int | None = None) -> list[dict[str, Any]]:
    start = re.search(r"<section\b[^>]*id=['\"]matchupweek['\"][^>]*>", page, re.I)
    if not start:
        raise ValueError("matchup section not found")
    fragment = page[start.start():]
    end = re.search(r"<section\b[^>]*id=['\"]scoreboard['\"]", fragment, re.I)
    if end:
        fragment = fragment[:end.start()]
    status = "final" if re.search(r"Final results", fragment, re.I) else "unknown"
    rows: list[dict[str, Any]] = []
    row_pattern = re.compile(r"<li\b([^>]*data-target\s*=\s*(['\"])[^'\"]*matchup\?[^'\"]*\2[^>]*)>(.*?)</li>", re.I | re.S)
    for row_tag, _, body in row_pattern.findall(fragment):
        target = _attrs(row_tag).get("data-target", "")
        ids = re.search(r"mid1=(\d+).*?mid2=(\d+)", html.unescape(target))
        anchors = []
        for attrs_raw, content in re.findall(r"<a\b([^>]*)>(.*?)</a>", body, re.I | re.S):
            attrs = _attrs(attrs_raw)
            href_match = TEAM_HREF.search(attrs.get("href", ""))
            name = clean_text(content)
            if "F-link" in attrs.get("class", "").split() and href_match and name:
                anchors.append((int(href_match.group("team")), name))
        score_matches = re.findall(
            r"<div\b[^>]*class\s*=\s*(['\"])[^'\"]*\bFz-lg\b[^'\"]*\1[^>]*>(.*?)</div>",
            body,
            re.I | re.S,
        )
        scores = [_float(score_body) for _, score_body in score_matches]
        if len(anchors) != 2 or len(scores) < 2 or not ids:
            continue
        team_entries = []
        for team_id, name in anchors[:2]:
            team_key = f"{game_key}.l.{league_id}.t.{team_id}"
            team_entries.append({
                "yahoo_team_key": team_key,
                "franchise_id": mappings.get(team_key),
                "historical_team_name": name,
                "mapping_status": "verified" if mappings.get(team_key) else "unresolved",
                "score": scores[len(team_entries)],
            })
        a_score, b_score = team_entries[0]["score"], team_entries[1]["score"]
        tie = status == "final" and a_score is not None and a_score == b_score
        margin = round(abs(a_score - b_score), 2) if a_score is not None and b_score is not None else None
        winner = None
        winner_name = None
        if status == "final" and a_score is not None and b_score is not None and not tie:
            winner_index = 0 if a_score > b_score else 1
            winner = team_entries[winner_index]["franchise_id"]
            winner_name = team_entries[winner_index]["historical_team_name"]
        rows.append({
            "season": season,
            "week": week,
            "matchup_id": f"{season}-w{week:02d}-{min(int(ids.group(1)), int(ids.group(2))):02d}-{max(int(ids.group(1)), int(ids.group(2))):02d}",
            "status": status,
            "is_playoffs": bool(playoff_start_week and week >= playoff_start_week),
            "is_consolation": None,
            "team_a": team_entries[0],
            "team_b": team_entries[1],
            "winner_franchise_id": winner,
            "winner_historical_name": winner_name,
            "tie": tie,
            "margin": margin,
            "source": "official_yahoo_public_archive",
            "verified": status == "final" and a_score is not None and b_score is not None,
        })
    if not rows:
        raise ValueError(f"no valid matchups found for week {week}")
    return rows


def parse_draft(page: str, *, season: int, game_key: str, league_id: str,
                mappings_by_name: dict[str, str | None]) -> list[dict[str, Any]]:
    picks: list[dict[str, Any]] = []
    tables = re.findall(r"<table\b[^>]*>(.*?)</table>", page, re.I | re.S)
    for table in tables:
        round_match = re.search(r"Round\s+(\d+)", clean_text(table), re.I)
        if not round_match:
            continue
        round_number = int(round_match.group(1))
        for _, body in re.findall(r"<tr\b([^>]*)>(.*?)</tr>", table, re.I | re.S):
            cells = re.findall(r"<td\b([^>]*)>(.*?)</td>", body, re.I | re.S)
            if len(cells) != 3:
                continue
            round_pick_match = re.search(r"\d+", clean_text(cells[0][1]))
            player = re.search(r"<a\b([^>]*)>(.*?)</a>", cells[1][1], re.I | re.S)
            if not (round_pick_match and player):
                continue
            player_attrs = _attrs(player.group(1))
            player_name = clean_text(player.group(2))
            player_id_match = re.search(r"/players/(\d+)", player_attrs.get("href", ""))
            team_attrs = _attrs(cells[2][0])
            team_name = html.unescape(team_attrs.get("title") or clean_text(cells[2][1]))
            picks.append({
                "round": round_number,
                "round_pick": int(round_pick_match.group()),
                "overall_pick": None,
                "franchise_id": mappings_by_name.get(team_name.casefold()),
                "historical_team_name": team_name,
                "mapping_status": "verified" if mappings_by_name.get(team_name.casefold()) else "unresolved",
                "player_id": player_id_match.group(1) if player_id_match else None,
                "player_name": player_name,
                "source": "official_yahoo_public_archive",
            })
    for index, pick in enumerate(picks, start=1):
        pick["overall_pick"] = index
    if not picks:
        raise ValueError("draft results contained no valid picks")
    return picks


def parse_roster(page: str, *, season: int, week: int, team_key: str,
                 franchise_id: str | None, historical_team_name: str) -> list[dict[str, Any]]:
    players: list[dict[str, Any]] = []
    for table in re.findall(r"<table\b[^>]*id=['\"]statTable\d+['\"][^>]*>(.*?)</table>", page, re.I | re.S):
        for row_tag, body in re.findall(r"<tr\b([^>]*)>(.*?)</tr>", table, re.I | re.S):
            pos = re.search(r"data-pos=['\"]([^'\"]+)['\"]", body, re.I)
            player = re.search(r"<a\b([^>]*\bclass\s*=\s*(['\"])[^'\"]*\bname\b[^'\"]*\2[^>]*)>(.*?)</a>", body, re.I | re.S)
            score = re.search(r"<td\b[^>]*class\s*=\s*(['\"])[^'\"]*\bpts\b[^'\"]*\1[^>]*>(.*?)</td>", body, re.I | re.S)
            if not (pos and player and score):
                continue
            attrs = _attrs(player.group(1))
            player_id_match = re.search(r"/players/(\d+)", attrs.get("href", ""))
            players.append({
                "season": season,
                "week": week,
                "yahoo_team_key": team_key,
                "franchise_id": franchise_id,
                "historical_team_name": historical_team_name,
                "player_id": player_id_match.group(1) if player_id_match else None,
                "player_name": clean_text(player.group(3)),
                "selected_position": pos.group(1),
                "starter_or_bench": "bench" if pos.group(1) == "BN" or "bench" in _classes(row_tag) else "starter",
                "fantasy_points": _float(score.group(2)),
                "source": "official_yahoo_public_archive",
            })
    if not players:
        raise ValueError("roster page contained no scored players")
    return players


def parse_transactions(page: str, *, season: int, game_key: str, league_id: str,
                       mappings: dict[str, str | None], offset: int = 0) -> list[dict[str, Any]]:
    table = re.search(
        r"<table\b[^>]*class\s*=\s*(['\"])[^'\"]*\bTst-transaction-table\b[^'\"]*\1[^>]*>(.*?)</table>",
        page,
        re.I | re.S,
    )
    if not table:
        raise ValueError("transaction table not found")
    transactions: list[dict[str, Any]] = []
    for _, body in re.findall(r"<tr\b([^>]*)>(.*?)</tr>", table.group(2), re.I | re.S):
        action_titles = re.findall(r"title=['\"](Added Player|Dropped Player|Trade[^'\"]*)['\"]", body, re.I)
        team_link = re.search(
            r"<a\b([^>]*\bclass\s*=\s*(['\"])[^'\"]*\bTst-team-name\b[^'\"]*\2[^>]*)>(.*?)</a>",
            body,
            re.I | re.S,
        )
        timestamp = re.search(
            r"<span\b[^>]*class\s*=\s*(['\"])[^'\"]*\bF-timestamp\b[^'\"]*\1[^>]*>(.*?)</span>",
            body,
            re.I | re.S,
        )
        if not (action_titles and team_link and timestamp):
            continue
        team_attrs = _attrs(team_link.group(1))
        team_match = TEAM_HREF.search(team_attrs.get("href", ""))
        if not team_match:
            continue
        team_id = int(team_match.group("team"))
        team_key = f"{game_key}.l.{league_id}.t.{team_id}"
        players = []
        player_blocks = re.findall(r"<div\b[^>]*class\s*=\s*(['\"])[^'\"]*\bPbot-xs\b[^'\"]*\1[^>]*>(.*?)</div>", body, re.I | re.S)
        for player_index, (_, player_body) in enumerate(player_blocks):
            player_link = re.search(r"<a\b([^>]*)>(.*?)</a>", player_body, re.I | re.S)
            if not player_link:
                continue
            player_attrs = _attrs(player_link.group(1))
            player_id_match = re.search(r"/(?:players|teams)/([^/?'\"]+)", player_attrs.get("href", ""))
            detail = re.search(r"<span\b[^>]*class\s*=\s*(['\"])[^'\"]*\bF-position\b[^'\"]*\1[^>]*>(.*?)</span>", player_body, re.I | re.S)
            source = re.search(r"<h6\b[^>]*>(.*?)</h6>", player_body, re.I | re.S)
            detail_text = clean_text(detail.group(2)) if detail else ""
            nfl_team, position = (item.strip() for item in detail_text.split("-", 1)) if "-" in detail_text else (None, None)
            action = "add" if player_index == 0 and any("added" in value.casefold() for value in action_titles) else "drop"
            players.append({
                "action": action,
                "player_id": player_id_match.group(1) if player_id_match else None,
                "player_name": clean_text(player_link.group(2)),
                "nfl_team": nfl_team,
                "position": position,
                "source_or_destination": clean_text(source.group(1)) if source else None,
            })
        lowered_actions = {item.casefold() for item in action_titles}
        transaction_type = "add_drop" if any("added" in item for item in lowered_actions) and any("dropped" in item for item in lowered_actions) else (
            "add" if any("added" in item for item in lowered_actions) else (
                "drop" if any("dropped" in item for item in lowered_actions) else "trade"
            )
        )
        transactions.append({
            "transaction_id": f"{season}-t-{offset + len(transactions) + 1:04d}",
            "season": season,
            "display_timestamp": clean_text(timestamp.group(2)),
            "transaction_type": transaction_type,
            "yahoo_team_key": team_key,
            "franchise_id": mappings.get(team_key),
            "historical_team_name": clean_text(team_link.group(3)),
            "mapping_status": "verified" if mappings.get(team_key) else "unresolved",
            "players": players,
            "source": "official_yahoo_public_archive",
        })
    return transactions


def next_transaction_offset(page: str) -> int | None:
    match = re.search(r"href=['\"][^'\"]*transactionsfilter=all(?:&amp;|&)count=(\d+)['\"][^>]*>\s*Next", page, re.I)
    return int(match.group(1)) if match else None


@dataclass
class ArchiveClient:
    cache_root: pathlib.Path
    delay_seconds: float = 2.5
    max_retries: int = 4
    timeout_seconds: int = 45
    sleeper: Callable[[float], None] = time.sleep
    session: requests.Session | None = None

    def __post_init__(self) -> None:
        self.session = self.session or requests.Session()
        self.session.headers.update({"User-Agent": "RoadToGloryArchive/1.0 (+GitHub Pages data preservation)"})
        self._last_request_at = 0.0

    def get(self, url: str, cache_path: pathlib.Path, *, refresh: bool = False) -> str:
        path = self.cache_root / cache_path
        if path.exists() and not refresh:
            cached = path.read_text(encoding="utf-8")
            if is_login_page(cached):
                raise RuntimeError("Yahoo archive requires sign-in")
            return cached
        path.parent.mkdir(parents=True, exist_ok=True)
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            elapsed = time.monotonic() - self._last_request_at
            if elapsed < self.delay_seconds:
                self.sleeper(self.delay_seconds - elapsed)
            try:
                response = self.session.get(url, timeout=self.timeout_seconds)
                self._last_request_at = time.monotonic()
                if response.status_code == 429 or 500 <= response.status_code < 600:
                    retry_after = response.headers.get("Retry-After")
                    wait = float(retry_after) if retry_after and retry_after.isdigit() else min(60.0, 2 ** attempt + random.random())
                    last_error = RuntimeError(f"Yahoo archive temporarily unavailable (HTTP {response.status_code})")
                    if attempt < self.max_retries:
                        self.sleeper(wait)
                        continue
                response.raise_for_status()
                if is_login_page(response.text):
                    raise RuntimeError("Yahoo archive requires sign-in")
                path.write_text(response.text, encoding="utf-8")
                return response.text
            except requests.RequestException as error:
                last_error = RuntimeError(f"Yahoo archive request failed ({type(error).__name__})")
                if attempt < self.max_retries:
                    self.sleeper(min(60.0, 2 ** attempt + random.random()))
                    continue
                break
        raise last_error or RuntimeError("Yahoo archive request failed")


def write_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
