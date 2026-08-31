"""Fetch public NFL news without exposing feed failures in the site ticker."""

from __future__ import annotations

import json
import pathlib
import sys
import time
import xml.etree.ElementTree as ET
from typing import Any, Iterable


FEEDS = [
    ("NFL.com", "https://www.nfl.com/rss/rsslanding?searchCategory=news"),
    ("ESPN NFL", "https://www.espn.com/espn/rss/nfl/news"),
    ("FantasyPros", "https://www.fantasypros.com/rss/nfl-news.xml"),
]
MAX_ITEMS_PER_FEED = 8
OUTPUT_PATH = pathlib.Path("_data/news.json")
SCHEMA_VERSION = 1


def parse_feed(xml_bytes: bytes, source: str) -> list[dict[str, str]]:
    root = ET.fromstring(xml_bytes)
    items: list[dict[str, str]] = []

    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        if title and link:
            items.append(
                {
                    "source": source,
                    "title": title,
                    "link": link,
                    "published_at": published,
                }
            )

    if items:
        return items

    atom = {"a": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//a:entry", atom):
        title = (entry.findtext("a:title", namespaces=atom) or "").strip()
        link_element = entry.find("a:link", atom)
        link = (link_element.get("href") if link_element is not None else "").strip()
        published = (
            entry.findtext("a:updated", namespaces=atom)
            or entry.findtext("a:published", namespaces=atom)
            or ""
        ).strip()
        if title and link:
            items.append(
                {
                    "source": source,
                    "title": title,
                    "link": link,
                    "published_at": published,
                }
            )
    return items


def valid_items(payload: Any) -> list[dict[str, str]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        return []
    valid: list[dict[str, str]] = []
    for item in payload["items"]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        link = str(item.get("link") or "").strip()
        if title and link.startswith(("https://", "http://")):
            valid.append(item)
    return valid


def load_existing(path: pathlib.Path = OUTPUT_PATH) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def build_news_payload(
    feed_results: Iterable[tuple[str, list[dict[str, str]]]],
    *,
    existing: dict[str, Any] | None = None,
    updated_at: int | None = None,
) -> tuple[dict[str, Any], bool]:
    items: list[dict[str, str]] = []
    for _, feed_items in feed_results:
        items.extend(feed_items[:MAX_ITEMS_PER_FEED])

    if items:
        previous_items = valid_items(existing)
        if previous_items == items and existing is not None:
            return existing, False
        return {
            "schema_version": SCHEMA_VERSION,
            "updated": updated_at if updated_at is not None else int(time.time()),
            "items": items,
        }, True

    if valid_items(existing):
        return existing, False

    empty = {"schema_version": SCHEMA_VERSION, "updated": None, "items": []}
    return empty, existing != empty


def write_if_changed(path: pathlib.Path, payload: dict[str, Any]) -> bool:
    serialized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == serialized:
        print(f"unchanged {path}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8")
    temporary.replace(path)
    print(f"wrote {path}")
    return True


def main() -> None:
    import requests

    results: list[tuple[str, list[dict[str, str]]]] = []
    for source, url in FEEDS:
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            items = parse_feed(response.content, source)
            print(f"{source}: {len(items)} valid items")
            results.append((source, items))
        except (requests.RequestException, ET.ParseError, ValueError) as error:
            print(f"warning: {source} feed failed: {error}", file=sys.stderr)
            results.append((source, []))

    existing = load_existing()
    payload, should_write = build_news_payload(results, existing=existing)
    if should_write:
        write_if_changed(OUTPUT_PATH, payload)
    elif valid_items(existing):
        print("No new valid articles; preserved previous news data")
    else:
        print("No valid articles available; empty news data is already current")


if __name__ == "__main__":
    main()
