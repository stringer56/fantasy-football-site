import json, pathlib, time, requests, xml.etree.ElementTree as ET

FEEDS = [
  ("NFL.com", "https://www.nfl.com/rss/rsslanding?searchCategory=news"),
  ("ESPN NFL", "https://www.espn.com/espn/rss/nfl/news"),
  ("FantasyPros", "https://www.fantasypros.com/rss/nfl-news.xml"),
]
MAX_ITEMS_PER_FEED = 8

def parse_rss(xml_bytes, source):
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        link  = item.findtext("link") or ""
        pub   = item.findtext("pubDate") or ""
        if title and link:
            items.append({"source": source, "title": title.strip(), "link": link.strip(), "pubDate": pub})
    if not items:
        ns = {"a":"http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//a:entry", ns):
            title = (entry.findtext("a:title", namespaces=ns) or "").strip()
            link_el = entry.find("a:link", ns)
            link = (link_el.get("href") if link_el is not None else "").strip()
            pub = (entry.findtext("a:updated", namespaces=ns) or "")
            if title and link:
                items.append({"source": source, "title": title, "link": link, "pubDate": pub})
    return items

def main():
    all_items = []
    for (name, url) in FEEDS:
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            items = parse_rss(r.content, name)[:MAX_ITEMS_PER_FEED]
            all_items.extend(items)
        except Exception as e:
            all_items.append({"source": name, "title": f"[Feed error: {e}]", "link": "", "pubDate": ""})
    out = {"updated": int(time.time()), "items": all_items}
    pathlib.Path("_data").mkdir(exist_ok=True)
    pathlib.Path("_data/news.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote _data/news.json with", len(all_items), "items")

if __name__ == "__main__":
    main()
