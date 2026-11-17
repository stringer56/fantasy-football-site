"""Recover final Yahoo scores and keep recent completed weeks correction-aware.

Only Yahoo's explicit 'Final results' marks a week final. No current roster or
standing is copied into a historical week. Raw pages remain in ignored cache.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    from . import build_live_season as live
    from .yahoo_archive import ArchiveClient
    from .yahoo_live import _current_season_record, parse_current_week, parse_live_matchups
except ImportError:
    import build_live_season as live
    from yahoo_archive import ArchiveClient
    from yahoo_live import _current_season_record, parse_current_week, parse_live_matchups


def finalized_snapshot(previous, raw, by_key, h2h, thresholds, timestamp):
    week = raw['week']
    games = raw['matchups']
    keys = [team['team_key'] for game in games for team in game['teams']]
    if len(games) != 6 or len(keys) != 12 or set(keys) != set(by_key):
        raise ValueError(f'Week {week}: incomplete or unmapped slate')
    if any(game['status'] != 'postevent' or game['week'] != week for game in games):
        raise ValueError(f'Week {week}: Yahoo has not confirmed final results')
    if any(not isinstance(team.get('score'), (int, float)) for game in games for team in game['teams']):
        raise ValueError(f'Week {week}: missing final score')
    normalized = live.normalize_matchups(raw, {}, {}, by_key, h2h)
    old_teams = {team['team_key']: team for game in previous.get('matchups', []) for team in game['teams']}
    for game in normalized:
        for team in game['teams']:
            # Keep only the roster saved for this exact week, never today's.
            team['roster'] = old_teams.get(team['team_key'], {}).get('roster', []) if previous.get('week') == week else []
            team['record'] = old_teams.get(team['team_key'], {}).get('record')
    # Preserve participation/community snapshots independently of score repair.
    result = {**previous, 'schema_version': 1, 'season': 2026, 'week': week,
              'generated_at': timestamp, 'data_status': 'ready',
              'freshness': {'status': 'current', 'source_updated_at': timestamp,
                            'label': 'Final scores verified from Yahoo public scoreboard'},
              'matchups': normalized, 'standings': previous.get('standings', []),
              'weekly_facts': live.weekly_facts(normalized, []),
              'record_watch': live.record_watch_events(normalized, thresholds)}
    for field in ('power_rankings', 'picks', 'active_vote'):
        result.setdefault(field, None)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all', action='store_true', help='Recheck every completed week, including old finals')
    args = parser.parse_args()
    season, config = _current_season_record()
    current = live.load_json(live.GENERATED / 'matchups.json')['week']
    _, by_key = live.franchise_indexes(live.load_yaml(live.ROOT / '_data/franchises.yml'), season)
    h2h = live.load_json(live.GENERATED / 'records/head_to_head.json')
    thresholds = live.load_json(live.GENERATED / 'records/record_thresholds.json')
    client = ArchiveClient(live.ROOT / '.cache/yahoo-live/completed', delay_seconds=1, max_retries=1)
    updated = 0
    for week in range(1, current):
        path = live.GENERATED / 'live' / str(season) / f'week-{week:02d}.json'
        previous = live.load_json(path) if path.exists() else {}
        games = previous.get('matchups', [])
        if not args.all and week < current - 2 and len(games) == 6 and all(g.get('status') == 'final' for g in games):
            continue
        page = client.get(f"{config['league_url']}?module=matchups&lhst=matchups&matchup_week={week}", Path(f'week-{week:02d}.html'), refresh=True)
        if parse_current_week(page) != week:
            raise ValueError(f'Yahoo returned the wrong week for {week}')
        raw = {'week': week, 'matchups': parse_live_matchups(page, week=week, game_key=str(config['game_key']), league_id=str(config['league_id']))}
        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        result = finalized_snapshot(previous, raw, by_key, h2h, thresholds, timestamp)
        # Unchanged finals retain their original verification timestamp.
        if result['matchups'] == games and previous.get('freshness', {}).get('label') == result['freshness']['label']:
            continue
        live.write_json(path, result)
        updated += 1
        print(f'Verified final Week {week}: 6 matchups')
    print(f'Completed-week sync: {updated} archives updated')


if __name__ == '__main__':
    main()
