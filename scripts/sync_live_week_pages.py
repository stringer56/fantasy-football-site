"""Create tiny collection routes for normalized live-week snapshots."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIVE_ROOT = ROOT / "_data" / "generated" / "live"
PAGE_ROOT = ROOT / "_live_weeks"


def page_text(season: int, week: int) -> str:
    return f'''---
title: {season} Week {week}
season: {season}
season_key: "{season}"
week: {week}
data_key: week-{week:02d}
permalink: /{season}/week/{week}/
description: Road to Glory FFL Week {week} matchups, projections, rosters, notable facts, and Power Rankings.
---
'''


def sync_pages(live_root: Path = LIVE_ROOT, page_root: Path = PAGE_ROOT) -> list[Path]:
    created: list[Path] = []
    for snapshot in sorted(live_root.glob("[0-9][0-9][0-9][0-9]/week-*.json")):
        payload = json.loads(snapshot.read_text(encoding="utf-8"))
        season, week = payload.get("season"), payload.get("week")
        if not isinstance(season, int) or not isinstance(week, int):
            raise ValueError(f"{snapshot}: season and week must be integers")
        target = page_root / f"{season}-week-{week:02d}.md"
        expected = page_text(season, week)
        if target.exists() and target.read_text(encoding="utf-8") != expected:
            raise ValueError(f"refusing to overwrite non-generated live-week page: {target}")
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(expected, encoding="utf-8")
            created.append(target)
    return created


def main() -> None:
    created = sync_pages()
    print(f"Live-week routes ready: {len(list(PAGE_ROOT.glob('*.md')))} total, {len(created)} created")


if __name__ == "__main__":
    main()
