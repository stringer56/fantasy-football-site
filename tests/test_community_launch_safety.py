"""Synthetic CLI dry runs. Every output goes to an isolated temporary repository."""
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml
from scripts import voting_common, validate_privacy, build_community_forms

ROOT = Path(__file__).resolve().parents[1]


class CommunityCliDryRun(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / 'scripts', self.root / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))
        self.data = self.root / '_data'
        self.data.mkdir()
        self.deadline = '2020-09-01T20:20:00-04:00'
        self.published = '2020-09-02T10:00:00-04:00'
        self.write('site.yml', {'schema_version': 1, 'current_season': 2099})
        self.write('owners.yml', {'schema_version': 1, 'owners': [
            {'owner_id': 'test-owner-a', 'display_name': 'Synthetic A', 'active': True},
            {'owner_id': 'test-owner-b', 'display_name': 'Synthetic B', 'active': True}]})
        self.write('franchises.yml', {'schema_version': 1, 'franchises': [
            {'franchise_id': name, 'slug': name, 'name': name, 'status': 'active', 'branding': {},
             'yahoo': {'team_keys': {'2099': key}}}
            for name, key in [('test-alpha', 'x.t.1'), ('test-beta', 'x.t.2')]]})
        self.community = {'schema_version': 1, 'season': 2099,
                          'power_rankings': {'closes_at': self.deadline},
                          'pickem': {'lock_at': self.deadline, 'lock_week': 1}}
        self.write('community.yml', self.community)
        self.poll = {'vote_id': 'synthetic-poll', 'season': 2099, 'type': 'custom', 'title': 'Synthetic poll',
                     'description': 'SYNTHETIC_TEST_ONLY', 'status': 'closed',
                     'open_date': '2020-09-01T00:00:00-04:00', 'close_date': self.deadline,
                     'options': [{'id': 'yes', 'label': 'Yes'}, {'id': 'no', 'label': 'No'}],
                     'results_visibility': 'after_close'}
        self.write('votes.yml', {'schema_version': 1, 'polls': [self.poll]})
        self.matchups = {'schema_version': 1, 'week': 1, 'matchups': [{'status': 'preevent',
                         'teams': [{'team_key': 'x.t.1'}, {'team_key': 'x.t.2'}]}]}
        self.write('generated/matchups.json', self.matchups)
        self.write('generated/manifest.json', {'schema_version': 1, 'season': 2099, 'status': 'ready'})
        self.mid = '2099-week-01-test-alpha-vs-test-beta'

    def write(self, name, value):
        path = self.data / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) if name.endswith('.json') else yaml.safe_dump(value), encoding='utf-8')

    def csv(self, kind, rows):
        path = self.root / 'private-vote-imports' / f'{kind}-week-01.csv'
        path.parent.mkdir(exist_ok=True)
        with path.open('w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        return str(path)

    def cli(self, script, *args, ok=True):
        result = subprocess.run([sys.executable, str(self.root / 'scripts' / script), *args],
                                cwd=self.root, capture_output=True, text=True, encoding='utf-8',
                                env={**__import__('os').environ, 'PYTHONIOENCODING': 'utf-8'})
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result

    def row(self, owner='test-owner-a'):
        return {'submitted_at': '2020-09-01T10:00:00-04:00', 'owner_id': owner, 'season': 2099, 'week': 1}

    def test_power_complete_csv_preview_finalize_immutable_override_refresh(self):
        path = self.csv('power', [{**self.row(), 'rank_1': 'test-alpha', 'rank_2': 'test-beta'}])
        opts = [path, '--season', '2099', '--week', '1', '--deadline', self.deadline]
        final = [*opts, '--published-at', self.published]
        self.cli('finalize_power_rankings.py', *final, ok=False)
        self.cli('import_power_rankings.py', *opts)
        self.assertFalse((self.data / 'power_rankings').exists())
        self.cli('finalize_power_rankings.py', *final)
        archive = self.data / 'power_rankings/2099/week-01.json'
        first = archive.read_bytes()
        self.cli('finalize_power_rankings.py', *final)
        self.assertEqual(first, archive.read_bytes())
        payload = json.loads(first)
        self.assertTrue(all(row['movement'] is None for row in payload['rankings']))
        path = self.csv('power', [{**self.row(), 'rank_1': 'test-beta', 'rank_2': 'test-alpha'}])
        self.cli('finalize_power_rankings.py', *final, ok=False)
        self.cli('import_power_rankings.py', *opts)
        self.cli('finalize_power_rankings.py', *final, ok=False)
        self.cli('finalize_power_rankings.py', *final, '--override-finalized', ok=False)
        self.cli('finalize_power_rankings.py', *final, '--override-finalized', '--override-reason', 'Synthetic reviewed correction')
        self.assertEqual(json.loads(archive.read_text())['audit'][-1]['action'], 'override')
        self.cli('build_power_rankings.py', '--input', path, ok=False)

    def test_pick_complete_csv_lock_grade_binding_and_override(self):
        path = self.csv('picks', [{**self.row(), self.mid: 'test-alpha'}, {**self.row('test-owner-b'), self.mid: 'test-beta'}])
        opts = [path, '--season', '2099', '--week', '1']
        final = [*opts, '--lock-at', self.deadline, '--published-at', self.published]
        self.cli('finalize_pickem.py', *final, ok=False)
        self.cli('import_pickem.py', *opts)
        self.assertFalse((self.data / 'picks').exists())
        self.cli('finalize_pickem.py', *final)
        archive = self.data / 'picks/2099/week-01.json'
        locked = json.loads(archive.read_text())
        self.assertFalse(locked['manager_results'])
        self.assertNotIn('input_sha256', locked)
        self.matchups['matchups'][0].update(status='postevent', winner_team_key='x.t.1')
        self.write('generated/matchups.json', self.matchups)
        # Equal aggregates but swapped manager picks must NOT grade without override.
        self.csv('picks', [{**self.row(), self.mid: 'test-beta'}, {**self.row('test-owner-b'), self.mid: 'test-alpha'}])
        self.cli('import_pickem.py', *opts)
        self.cli('finalize_pickem.py', *final, ok=False)
        self.csv('picks', [{**self.row(), self.mid: 'test-alpha'}, {**self.row('test-owner-b'), self.mid: 'test-beta'}])
        self.cli('import_pickem.py', *opts)
        self.cli('finalize_pickem.py', *final)
        graded = json.loads(archive.read_text())
        self.assertEqual(graded['state'], 'final')
        self.assertEqual(graded['audit'][-1]['action'], 'graded')
        self.assertEqual(graded['weekly_winners'][0]['owner_id'], 'test-owner-a')
        self.assertTrue(all(not row['picks'] for row in graded['manager_results']))
        self.cli('build_picks_leaderboard.py')
        rebuilt = json.loads((self.data / 'generated/picks.json').read_text())
        self.assertEqual(rebuilt['leaderboard'][0]['correct'], 1)
        self.cli('build_picks_leaderboard.py', '--input', path, ok=False)

    def test_general_csv_preview_finalize_archive_and_later_poll_preservation(self):
        path = self.csv('votes', [{'submitted_at': self.row()['submitted_at'], 'owner_id': 'test-owner-a', 'vote_id': 'synthetic-poll', 'option_id': 'yes'}])
        self.cli('import_vote_results.py', '--input', path, '--publish', '--published-at', self.published, ok=False)
        self.cli('import_vote_results.py', '--input', path)
        self.assertFalse((self.data / 'league_votes').exists())
        self.cli('import_vote_results.py', '--input', path, '--publish', '--published-at', self.published)
        archive = self.data / 'league_votes/2099/synthetic-poll.json'
        self.assertEqual(json.loads(archive.read_text())['ballots_counted'], 1)
        poll2 = {**self.poll, 'vote_id': 'synthetic-second-poll'}
        self.write('votes.yml', {'schema_version': 1, 'polls': [self.poll, poll2]})
        path2 = self.csv('votes', [{'submitted_at': self.row()['submitted_at'], 'owner_id': 'test-owner-a', 'vote_id': poll2['vote_id'], 'option_id': 'no'}])
        self.cli('import_vote_results.py', '--input', path2)
        self.cli('import_vote_results.py', '--input', path2, '--publish', '--published-at', self.published)
        output = json.loads((self.data / 'generated/votes.json').read_text())
        self.assertEqual(len(output['archived_polls']), 2)
        self.assertTrue(all(poll['ballots_counted'] == 1 for poll in output['archived_polls']))
        self.csv('votes', [{'submitted_at': self.row()['submitted_at'], 'owner_id': 'test-owner-a', 'vote_id': poll2['vote_id'], 'option_id': 'yes'}])
        self.cli('import_vote_results.py', '--input', path2)
        self.cli('import_vote_results.py', '--input', path2, '--publish', '--published-at', self.published, ok=False)
        self.cli('import_vote_results.py', '--input', path2, '--publish', '--published-at', self.published,
                 '--override-finalized', '--override-reason', 'Synthetic reviewed correction')
        changed = json.loads((self.data / 'league_votes/2099/synthetic-second-poll.json').read_text())
        self.assertEqual(changed['audit'][-1]['action'], 'override')

    def test_changed_config_or_deadline_invalidates_review(self):
        path = self.csv('power', [{**self.row(), 'rank_1': 'test-alpha', 'rank_2': 'test-beta'}])
        opts = [path, '--season', '2099', '--week', '1']
        self.cli('import_power_rankings.py', *opts)
        self.community['power_rankings']['closes_at'] = '2020-09-01T21:00:00-04:00'
        self.write('community.yml', self.community)
        self.cli('finalize_power_rankings.py', *opts, '--published-at', self.published, ok=False)


class LaunchBoundaryTests(unittest.TestCase):
    def test_future_lock_cannot_be_bypassed_by_future_publication(self):
        with self.assertRaises(ValueError):
            voting_common.require_lock_reached('2099-09-01T20:20:00-04:00', '2099-09-02T00:00:00Z')

    def test_duplicate_csv_headers_and_row_width_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.csv'
            for text in ['owner_id,owner_id\na,b\n', 'owner_id,week\na,1,2\n']:
                path.write_text(text)
                with self.assertRaises(voting_common.BallotError):
                    voting_common.load_import(path)

    def test_privacy_scan_catches_prohibited_values_without_echoing_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for content in ['private@example.com', 'https://docs.google.com/spreadsheets/d/private/edit', 'SYNTHETIC_TEST_ONLY', 'access_token: abcdefgh12345']:
                (root / 'index.html').write_text(content)
                errors = validate_privacy.scan(root, built=True)
                self.assertTrue(errors)
                self.assertNotIn(content, str(errors))

    def test_forms_helper_has_canonical_questions_and_no_invented_poll(self):
        config = build_community_forms.build_config()
        power, picks, votes = config['forms']
        self.assertEqual(len(power['questions']), 15)
        self.assertEqual(len(picks['questions']), 9)
        self.assertEqual(votes['questions'][1]['choices'], [])
        self.assertEqual(votes['questions'][2]['choices'], [])
        self.assertEqual(len(power['questions'][0]['choices']), 12)

    def test_only_safe_responder_url_shapes_are_accepted(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        self.addCleanup(lambda: sys.path.remove(str(ROOT / 'scripts')))
        from validate_votes_data import valid_public_form_url
        for url in ['https://docs.google.com/forms/d/e/example/viewform', 'https://forms.gle/example']:
            self.assertTrue(valid_public_form_url(url))
        for url in ['https://docs.google.com/forms/d/example/edit',
                    'https://docs.google.com/forms/d/example/formResponse',
                    'https://docs.google.com/forms/d/e/example/viewform?edit2=private',
                    'https://docs.google.com/forms/d/e/example/viewform?entry.1=private',
                    'https://docs.google.com/spreadsheets/d/example/edit',
                    'https://forms.gle/example?secret=private', 'http://forms.gle/example']:
            self.assertFalse(valid_public_form_url(url), url)

    def test_updater_does_not_stage_an_absent_ballot_archive(self):
        workflow = (ROOT / '.github/workflows/update.yml').read_text()
        self.assertNotIn('git add _data/generated _data/power_rankings', workflow)
        self.assertIn('if [ -e "$path" ]; then git add -- "$path"; fi', workflow)


if __name__ == '__main__':
    unittest.main()
