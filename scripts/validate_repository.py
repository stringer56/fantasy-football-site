"""Parse repository YAML, JSON, and page front matter."""

from __future__ import annotations

import json
import pathlib
import sys

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
SKIPPED_DIRECTORIES = {".git", ".venv", "_site", "vendor"}


def repository_files(pattern: str):
    for path in ROOT.rglob(pattern):
        if not any(part in SKIPPED_DIRECTORIES for part in path.parts):
            yield path


def validate_yaml(path: pathlib.Path) -> None:
    yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_json(path: pathlib.Path) -> None:
    json.loads(path.read_text(encoding="utf-8"))


def validate_front_matter(path: pathlib.Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return
    closing = text.find("\n---\n", 4)
    if closing == -1:
        raise ValueError("front matter has no closing delimiter")
    yaml.safe_load(text[4:closing])


def main() -> None:
    errors: list[str] = []
    checked = 0
    validators = [
        (("*.yml", "*.yaml"), validate_yaml),
        (("*.json",), validate_json),
        (("*.md", "*.html"), validate_front_matter),
    ]

    for patterns, validator in validators:
        for pattern in patterns:
            for path in repository_files(pattern):
                checked += 1
                try:
                    validator(path)
                except (ValueError, OSError, json.JSONDecodeError, yaml.YAMLError) as error:
                    errors.append(f"{path.relative_to(ROOT)}: {error}")

    if errors:
        print("Repository validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Parsed {checked} YAML, JSON, Markdown, and HTML files")


if __name__ == "__main__":
    main()
