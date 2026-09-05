"""Refresh public community views from configuration and finalized archives only."""
import subprocess
import sys

try:
    from . import import_vote_results as votes
    from .voting_common import load_yaml, write_json, ROOT
except ImportError:
    import import_vote_results as votes
    from voting_common import load_yaml, write_json, ROOT


def main():
    for script in ("build_power_rankings.py", "build_picks_leaderboard.py"):
        subprocess.run([sys.executable, str(ROOT / "scripts" / script)], check=True, cwd=ROOT)
    payload = votes.build_output(load_yaml("votes.yml"), load_yaml("owners.yml"),
                                archived_polls=votes.load_archives(), community=load_yaml("community.yml"))
    write_json(votes.OUTPUT_PATH, payload)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_live_season.py")], check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
