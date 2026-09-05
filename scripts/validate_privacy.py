"""Fail closed on private input, credential values and synthetic content in public files."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import yaml

try:
    from .validate_public_data import validate_payload
except ImportError:
    from validate_public_data import validate_payload

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "email address": r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
    "private Google URL": r"https?://docs\.google\.com/(?:spreadsheets/|forms/[^\s\"<>]*?(?:/edit|/formResponse|edit2=|entry\.))",
    "credential value": r'(?i)(?:access_token|refresh_token|client_secret|authorization)[\"\s]*[:=][\"\s]*(?:Bearer\s+)?[A-Za-z0-9_./+-]{8,}',
    "private Yahoo URL": r"(?i)(?:[?&](?:ikey|invitation_key)=|/invitation\?)",
    "synthetic ballot": r"(?i)(?:test-owner-[ab]|test-alpha|test-beta|SYNTHETIC_TEST_ONLY)",
    "raw response CSV": r"owner_id,submitted_at,season,week",
}


def scan(root: Path, *, built: bool = False) -> list[str]:
    errors = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if built and relative.parts[0] in {"private-vote-imports", "tests", "scripts", "tools", "docs", ".cache"}:
            errors.append(f"{relative}: non-public directory in build")
        if path.suffix.lower() == ".csv":
            errors.append(f"{relative}: CSV is prohibited in public output")
        if path.suffix.lower() not in {".json", ".yml", ".yaml", ".html", ".js", ".txt", ".csv", ".xml"}:
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in PATTERNS.items():
            if re.search(pattern, text):
                errors.append(f"{relative}: prohibited {label}")
        if not built and path.suffix in {".json", ".yml", ".yaml"}:
            payload = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
            errors.extend(validate_payload(relative, payload))
            # Internal aggregates belong only in private preview memory.
            if isinstance(payload, dict) and path.name == "picks.json":
                for week in [payload.get("current_week"), *(payload.get("weekly_results") or [])]:
                    if not week:
                        continue
                    if week.get("selection_totals"):
                        errors.append(f"{relative}: private preview totals present")
                    if week.get("state") not in {"locked", "final"} and (week.get("manager_results") or any(game.get("pick_results") for game in week.get("matchups", []))):
                        errors.append(f"{relative}: picks exposed before lock")
                    if week.get("manager_picks_visibility") != "public" and any(row.get("picks") for row in week.get("manager_results", [])):
                        errors.append(f"{relative}: private individual picks present")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path)
    args = parser.parse_args()
    errors = scan(ROOT / "_data")
    if args.site:
        if not args.site.is_dir():
            raise SystemExit("Built site directory is missing")
        errors += scan(args.site, built=True)
    if errors:
        raise SystemExit("Privacy validation failed:\n- " + "\n- ".join(errors))
    print("Privacy checks passed: public data" + (" and rendered artifact" if args.site else ""))


if __name__ == "__main__":
    main()
