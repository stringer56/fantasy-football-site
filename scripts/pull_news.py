"""Fetch public NFL news without exposing feed failures in the site ticker."""

from __future__ import annotations

import json
import pathlib
import sys
import time
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
from typing import Any, Iterable


FEEDS = [
    ("CBS Sports NFL", "https://www.cbssports.com/rss/headlines/nfl/"),
    ("RotoWire NFL", "https://www.rotowire.com/rss/news.php?sport=NFL"),
]
CATEGORIES = {"CBS Sports NFL": "nfl", "RotoWire NFL": "fantasy"}
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
        try:
            parsed = urlsplit(link)
        except ValueError:
            continue
        if title and parsed.scheme in {"https", "http"} and parsed.hostname and not parsed.username and not parsed.password and 'feed error' not in title.lower():
            # Explicit allowlist: never retain RSS description/content or unknown keys.
            valid.append({"source": str(item.get("source") or ""),
                          "title": re.sub(r'<[^>]*>', '', title)[:300], "link": link,
                          "published_at": str(item.get("published_at") or ""),
                          "category": CATEGORIES.get(item.get("source"), item.get("category", "nfl"))})
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
    previous = valid_items(existing)
    any_fresh = False
    for source, feed_items in feed_results:
        safe = valid_items({"items": feed_items})
        any_fresh = any_fresh or bool(safe)
        items.extend(safe or [i for i in previous if i['source'] == source])

    if not any_fresh and previous:
        # Preserve safe legacy snapshots byte-for-byte; scrub unexpected private/body fields.
        allowed = {"source", "title", "link", "published_at", "category"}
        if all(set(i) <= allowed for i in existing['items']) and len(previous) == len(existing['items']):
            return existing, False
        items = previous

    for item in items:
        raw = item['published_at']
        try:
            stamp = datetime.fromisoformat(raw.replace('Z', '+00:00')) if re.match(r'^\d{4}-\d{2}-\d{2}T', raw) else parsedate_to_datetime(raw)
            item['published_at'] = stamp.replace(tzinfo=stamp.tzinfo or timezone.utc).astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        except (ValueError, TypeError, OverflowError):
            item['published_at'] = ''
    items.sort(key=lambda i: (i['published_at'], i['link']), reverse=True)
    items = list({item['link']: item for item in items}.values())
    counts: dict[str, int] = {}
    limited = []
    for item in items:
        source = item['source']
        counts[source] = counts.get(source, 0) + 1
        if counts[source] <= MAX_ITEMS_PER_FEED:
            limited.append(item)
    items = limited

    if items:
        previous_items = existing.get('items', []) if existing else []
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
