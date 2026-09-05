"""Optional Playwright smoke review of a live URL or a local Jekyll artifact."""
import argparse
import functools
import http.server
import json
from pathlib import Path
import threading
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright
import yaml

ROUTES = ["", "2026/", "2026/week/1/", "power-rankings/", "picks/", "pickem/", "votes/", "teams/",
          "teams/van-cortlant-rangers/", "history/", "history/2024/", "records/", "drafts/", "cup/", "retired/", "rules/"]
WIDTHS = [1440, 1024, 768, 390, 360]


def review_routes(all_franchises=False):
    routes = list(ROUTES)
    if all_franchises:
        data = yaml.safe_load((Path(__file__).resolve().parents[1] / '_data/franchises.yml').read_text(encoding='utf-8'))
        routes.extend(f"{'retired' if row['status'] == 'retired' else 'teams'}/{row['slug']}/" for row in data['franchises'])
        routes.append('retired/quahog-stripes/')
    return list(dict.fromkeys(routes))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="https://stringer56.github.io/fantasy-football-site/")
    parser.add_argument("--site", type=Path)
    parser.add_argument("--browser", default=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--all-franchises", action="store_true", help="Review every active/retired franchise and Quahog identity")
    args = parser.parse_args()
    server = None
    if args.site:
        class Handler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                self.path = self.path.removeprefix("/fantasy-football-site") or "/"
                super().do_GET()
            def log_message(self, *args):
                pass
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(args.site.resolve())))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        args.url = f"http://127.0.0.1:{server.server_port}/fantasy-football-site/"
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.browser, headless=True,
                                    ignore_default_args=["--headless=old"], args=["--headless=new"])
        for width in WIDTHS:
            page = browser.new_page(viewport={"width": width, "height": 900})
            failed = []
            page.on("response", lambda response: failed.append(response.url) if response.status >= 400 and urlsplit(response.url).netloc == urlsplit(args.url).netloc else None)
            page.on("requestfailed", lambda request: failed.append(request.url) if urlsplit(request.url).netloc == urlsplit(args.url).netloc else None)
            for route in review_routes(args.all_franchises):
                failed.clear()
                response = page.goto(args.url + route, wait_until="networkidle")
                page.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager')")
                page.wait_for_function("[...document.images].every(i => i.complete)")
                menu_ok = True
                if page.locator('.nav-toggle').is_visible():
                    page.locator('.nav-toggle').click()
                    menu_ok = page.locator('.nav-toggle').get_attribute('aria-expanded') == 'true'
                    menu_ok = menu_ok and page.locator('#primary-navigation a').first.is_visible()
                    page.keyboard.press('Escape')
                    menu_ok = menu_ok and page.locator('.nav-toggle').get_attribute('aria-expanded') == 'false'
                checks = page.evaluate("""() => ({
                    overflow: document.documentElement.scrollWidth > innerWidth + 1,
                    brokenImages: [...document.images].filter(i => !i.complete || !i.naturalWidth).length,
                    missingAlt: [...document.images].filter(i => !i.hasAttribute('alt')).length,
                    title: document.title,
                    description: !!document.querySelector('meta[name="description"]'),
                    synthetic: /test-owner-[ab]|test-alpha|test-beta|SYNTHETIC_TEST_ONLY/i.test(document.body.innerText),
                    debugState: /\\bunconfigured\\b|missing JSON|importer unavailable/.test(document.querySelector('main')?.innerText || ''),
                    h1: document.querySelectorAll('h1').length
                    ,distortedTeamImages: [...document.querySelectorAll('.franchise-identity img, .franchise-card__image img, .retired-card__image img')].filter(i => getComputedStyle(i).objectFit !== 'contain').length
                    ,escapedTeamImages: [...document.querySelectorAll('.franchise-identity img, .franchise-card__image img')].filter(i => { const r=i.getBoundingClientRect(), p=i.parentElement.getBoundingClientRect(); return r.top < p.top-1 || r.bottom > p.bottom+1 || r.left < p.left-1 || r.right > p.right+1; }).length
                    ,missingPageAnchors: [...document.querySelectorAll('a[href^="#"]')].filter(a => a.hash.length > 1 && !document.getElementById(decodeURIComponent(a.hash.slice(1)))).length
                })""")
                checks.update({"width": width, "route": route, "status": response.status, "failedInternal": list(failed), "mobileMenu": menu_ok})
                results.append(checks)
                if (args.all_franchises or route in {"", "picks/", "power-rankings/", "votes/", "2026/week/1/"}) and width in {1440, 390, 360}:
                    page.screenshot(path=str(args.output / f"{route.replace('/', '-') or 'home'}-{width}.png"), full_page=True)
                    page.screenshot(path=str(args.output / f"{route.replace('/', '-') or 'home'}-{width}-cover.png"))
            page.close()
        browser.close()
    if server:
        server.shutdown()
    (args.output / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    problems = [r for r in results if r["overflow"] or r["brokenImages"] or r["missingAlt"] or r["synthetic"] or r["debugState"] or r["status"] != 200 or r["failedInternal"] or not r["mobileMenu"] or r["h1"] != 1 or r["distortedTeamImages"] or r["escapedTeamImages"] or r["missingPageAnchors"]]
    print(json.dumps({"checks": len(results), "problems": problems}, indent=2))
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
