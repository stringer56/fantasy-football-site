"""Generate an optional commissioner-only Apps Script from canonical IDs and slate."""
import argparse
import json
from pathlib import Path

try:
    from .voting_common import ROOT, load_yaml, active_franchises, owner_index, parse_deadline
    from .build_picks_leaderboard import canonical_matchups_from_yahoo
except ImportError:
    from voting_common import ROOT, load_yaml, active_franchises, owner_index, parse_deadline
    from build_picks_leaderboard import canonical_matchups_from_yahoo


def build_config():
    site, community = load_yaml('site.yml'), load_yaml('community.yml')
    season = site['current_season']
    data = json.loads((ROOT / '_data/generated/matchups.json').read_text(encoding='utf-8'))
    manifest = json.loads((ROOT / '_data/generated/manifest.json').read_text(encoding='utf-8'))
    franchises = load_yaml('franchises.yml')
    matchups, status = canonical_matchups_from_yahoo(data, manifest, season, franchises)
    if status != 'ready' or not matchups:
        raise ValueError('Verified canonical Yahoo slate is required to create Pick’em questions')
    week = data['week']
    pickem = community['pickem']
    if community['season'] != season or pickem.get('lock_week') != week:
        raise ValueError('Configure the verified Pick’em lock for this season/week before generating Forms')
    if pickem.get('lock_timezone') != 'America/New_York' or not parse_deadline(pickem.get('lock_at')):
        raise ValueError('A timezone-aware verified Pick’em lock in America/New_York is required')
    owners = owner_index(load_yaml('owners.yml'))
    teams = active_franchises(franchises)
    def question(title, choices, type='dropdown', help=''):
        return dict(title=title, choices=choices, type=type, help=help)
    manager = question('owner_id', list(owners), help='; '.join(f"{key} = {value['display_name']}" for key, value in owners.items()))
    base = [manager, question('season', [str(season)]), question('week', [str(week)])]
    ids = [team['franchise_id'] for team in teams]
    names = '; '.join(f"{team['franchise_id']} = {team['name']}" for team in teams)
    polls = [poll for poll in load_yaml('votes.yml')['polls'] if poll['status'] == 'open' and poll['season'] == season]
    # A reusable Form must not mix different option sets in one question.
    poll = polls[0] if len(polls) == 1 else None
    return {'season': season, 'week': week, 'forms': [
        {'kind': 'power', 'title': 'Road to Glory FFL — Weekly Power Rankings',
         'description': 'Rank every franchise exactly once. Latest valid submission per manager counts. Commissioner must announce the deadline.',
         'questions': base + [question(f'rank_{i}', ids, help=names) for i in range(1, len(ids)+1)]},
        {'kind': 'picks', 'title': "Road to Glory FFL — Weekly Pick'em",
         'description': f"Whole slate closes {community['pickem']['lock_at']} (America/New_York). Pick every matchup. Individual selections remain private.",
         'questions': base + [question(game['matchup_id'], [team['franchise_id'] for team in game['participants']], 'choice', ' vs '.join(team['display_name'] for team in game['participants'])) for game in matchups]},
        {'kind': 'votes', 'title': 'Road to Glory FFL — League Votes',
         'description': 'Commissioner must configure one real poll and its exact options before publishing. No poll is invented by this helper.',
         'questions': [manager, question('vote_id', [poll['vote_id']] if poll else []),
                       question('option_id', [option['id'] for option in poll['options']] if poll else [], 'choice')]},
    ]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    template = (ROOT / 'tools/community_forms.template.gs').read_text(encoding='utf-8')
    content = template.replace('__RTG_CONFIG__', json.dumps(build_config(), indent=2, ensure_ascii=False))
    output = ROOT / 'tools/create_community_forms.gs'
    if args.check:
        if not output.exists() or output.read_text(encoding='utf-8') != content:
            raise SystemExit('Apps Script helper is stale; run build_community_forms.py')
    else:
        output.write_text(content, encoding='utf-8')
    print('Verified canonical Form questions; no Forms created and no responses submitted.')


if __name__ == '__main__':
    main()
