"""Helper-only regression checks; no Forms or production responses are created."""
import copy
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_community_forms as forms


class CommunityFormHelperTests(unittest.TestCase):
    def config_with(self, **changes):
        load = forms.load_yaml
        community = copy.deepcopy(load('community.yml'))
        community['pickem'].update(changes)
        with patch.object(forms, 'load_yaml', side_effect=lambda name: community if name == 'community.yml' else load(name)):
            return forms.build_config()

    def test_old_week_lock_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'season/week'):
            self.config_with(lock_week=99)

    def test_missing_or_naive_lock_is_rejected(self):
        for value in [None, '', '2026-09-09T20:20:00']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.config_with(lock_at=value)

    def test_question_titles_follow_import_contract(self):
        config = forms.build_config()
        power, picks, votes = config['forms']
        self.assertEqual([q['title'] for q in power['questions']],
                         ['owner_id', 'season', 'week'] + [f'rank_{i}' for i in range(1, 13)])
        self.assertEqual([q['title'] for q in votes['questions']], ['owner_id', 'vote_id', 'option_id'])
        self.assertEqual([q['title'] for q in picks['questions'][:3]], ['owner_id', 'season', 'week'])
        ids = set(power['questions'][3]['choices'])
        for question in picks['questions'][3:]:
            self.assertEqual(len(question['choices']), 2)
            self.assertTrue(set(question['choices']) <= ids)
            self.assertEqual(question['title'], f"{config['season']}-week-{config['week']:02d}-" + '-vs-'.join(sorted(question['choices'])))

    @unittest.skipUnless(shutil.which('node'), 'Node is needed for Apps Script service-double execution')
    def test_creation_and_rerun_with_mock_google_services(self):
        result = subprocess.run(['node', str(ROOT / 'tests/fixtures/community/forms_runtime.cjs'),
                                 str(ROOT / 'tools/create_community_forms.gs')],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
