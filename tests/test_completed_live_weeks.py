import copy
import unittest
from scripts import build_live_season as live
from scripts.sync_completed_live_weeks import finalized_snapshot
from scripts.yahoo_live import parse_live_matchups


class CompletedWeeksTests(unittest.TestCase):
    def test_long_yahoo_navigation_does_not_hide_final_or_upcoming_status(self):
        row = ('<li data-target="/matchup?mid1=1&mid2=2">'
               '<a class="F-link" href="/f1/26455/1">A</a><a class="F-link" href="/f1/26455/2">B</a>'
               '<div class="Fz-lg">120.5</div><div class="F-shade">100</div>'
               '<div class="Fz-lg">99</div><div class="F-shade">101</div></li>')
        for heading, status in [('Final results', 'postevent'), ('Not started yet', 'preevent')]:
            page = '<section id="matchupweek">' + '<option>Week</option>' * 400 + '<h3>' + heading + '</h3>' + row + '</section><section id="scoreboard">'
            result = parse_live_matchups(page, week=10, game_key='470', league_id='26455')[0]
            self.assertEqual(result['status'], status)
            self.assertEqual(result['winner_team_key'], '470.l.26455.t.1' if status == 'postevent' else None)

    def fixtures(self):
        _, by_key = live.franchise_indexes(live.load_yaml(live.ROOT / '_data/franchises.yml'), 2026)
        keys = list(by_key)
        raw = {'week': 3, 'matchups': [{'week': 3, 'status': 'postevent', 'winner_team_key': keys[i], 'teams': [
            {'team_key': keys[i], 'score': 120.5}, {'team_key': keys[i+1], 'score': 99.0}]} for i in range(0, 12, 2)]}
        return raw, by_key

    def test_final_scores_replace_partial_scores_without_current_rosters(self):
        raw, mapping = self.fixtures()
        snapshot = finalized_snapshot({}, raw, mapping, {}, {}, '2026-11-17T00:00:00Z')
        self.assertEqual(len(snapshot['matchups']), 6)
        self.assertTrue(all(g['status'] == 'final' and g['winner_franchise_id'] for g in snapshot['matchups']))
        self.assertTrue(all(t['roster'] == [] and t['record'] is None for g in snapshot['matchups'] for t in g['teams']))
        self.assertEqual(snapshot['standings'], [])
        snapshot['picks'] = {'preserved': True}
        snapshot['matchups'][0]['teams'][0]['roster'] = [{'player_name': 'TEST ONLY'}]
        refreshed = finalized_snapshot(snapshot, raw, mapping, {}, {}, '2026-11-18T00:00:00Z')
        self.assertEqual(refreshed['picks'], snapshot['picks'])
        self.assertEqual(refreshed['matchups'][0]['teams'][0]['roster'], [{'player_name': 'TEST ONLY'}])

    def test_incomplete_nonfinal_missing_or_unmapped_scores_rejected(self):
        raw, mapping = self.fixtures()
        for mutate in [lambda d:d['matchups'].pop(), lambda d:d['matchups'][0].update(status='midevent'),
                       lambda d:d['matchups'][0]['teams'][0].update(score=None),
                       lambda d:d['matchups'][0]['teams'][0].update(team_key='unknown')]:
            changed = copy.deepcopy(raw)
            mutate(changed)
            with self.assertRaises(ValueError):
                finalized_snapshot({}, changed, mapping, {}, {}, '2026-11-17T00:00:00Z')
