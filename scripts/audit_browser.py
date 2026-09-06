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
WIDTHS = [1440, 1024, 768, 430, 390, 360]
LAUNCH_SHOTS = {
    (1440, ''), (1024, ''), (430, ''), (390, ''), (360, ''),
    (1440, 'teams/'), (360, 'teams/'),
    (1024, 'teams/albany-kneelers/'), (390, 'teams/greendale-human-beings/'),
    (430, 'retired/'), (1440, 'history/2024/'), (360, 'history/2024/'),
    (430, 'cup/'), (1024, 'records/'), (390, 'drafts/2025/'),
    (360, 'votes/'), (1440, 'rules/'),
}


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
    parser.add_argument("--all-routes", action="store_true", help="Review every HTML route in --site, including compatibility routes")
    parser.add_argument("--widths", default=','.join(map(str, WIDTHS)), help="Comma-separated viewport widths")
    parser.add_argument("--screenshots", choices=('all', 'representative', 'none'), default='all', help="Capture all views or only the launch-review selections")
    args = parser.parse_args()
    try:
        widths = [int(value) for value in args.widths.split(',')]
        if not widths or any(width < 320 for width in widths):
            raise ValueError
    except ValueError:
        parser.error('--widths must contain integer widths of at least 320 pixels')
    if args.all_routes and not args.site:
        parser.error("--all-routes requires the built --site artifact")
    routes = review_routes(args.all_franchises)
    if args.all_routes:
        routes = sorted({
            str(path.relative_to(args.site)).replace("\\", "/").removesuffix("index.html")
            for path in args.site.rglob("*.html")
        })
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
        for width in widths:
            page = browser.new_page(viewport={"width": width, "height": 900})
            failed = []
            script_errors = []
            page.on('pageerror', lambda error: script_errors.append(str(error)))
            page.on("response", lambda response: failed.append(response.url) if response.status >= 400 and urlsplit(response.url).netloc == urlsplit(args.url).netloc else None)
            page.on("requestfailed", lambda request: failed.append(request.url) if urlsplit(request.url).netloc == urlsplit(args.url).netloc else None)
            for route in routes:
                failed.clear()
                script_errors.clear()
                response = page.goto(args.url + route, wait_until="networkidle")
                page.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager')")
                page.wait_for_function("[...document.images].every(i => i.complete)")
                menu_ok = True
                expanded_overflow = False
                if page.locator('.nav-toggle').is_visible():
                    page.locator('.nav-toggle').click()
                    menu_ok = page.locator('.nav-toggle').get_attribute('aria-expanded') == 'true'
                    menu_ok = menu_ok and page.locator('#primary-navigation a').first.is_visible()
                    page.keyboard.press('Escape')
                    menu_ok = menu_ok and page.locator('.nav-toggle').get_attribute('aria-expanded') == 'false'
                    menu_ok = menu_ok and page.locator('.nav-toggle').evaluate("(el) => el === document.activeElement")
                disclosure = page.locator('main details:not([open]) > summary').first
                if disclosure.count():
                    disclosure_handle = disclosure.element_handle()
                    disclosure_handle.click()
                    disclosure_handle.evaluate("el => new Promise(resolve => requestAnimationFrame(() => resolve(el.parentElement.open)))")
                    expanded_overflow = page.evaluate("document.documentElement.scrollWidth > innerWidth + 1")
                    disclosure_handle.click()
                    page.evaluate("scrollTo(0, 0)")
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
                    ,unreadableLiveCards: [...document.querySelectorAll('.franchise-live__grid > article > p')].filter(n => getComputedStyle(n).color === getComputedStyle(n.parentElement).backgroundColor).length
                    ,overlappingSeasonCaption: [...document.querySelectorAll('.season-final-score')].filter(n => { const caption=n.parentElement.querySelector('figcaption'); return caption && caption.getBoundingClientRect().bottom > n.getBoundingClientRect().top + 1; }).length
                    ,overlappingFieldCaption: [...document.querySelectorAll('.franchise-card__visual')].filter(n => { const caption=n.querySelector('.franchise-card__venue span'), art=n.querySelector('.franchise-card__image'); return caption && art && caption.getBoundingClientRect().top < art.getBoundingClientRect().bottom - 1; }).length
                })""")
                checks.update({"width": width, "route": route, "status": response.status, "failedInternal": list(failed), "scriptErrors": list(script_errors), "mobileMenu": menu_ok, "expandedOverflow": expanded_overflow})
                checks['imageUsage'] = page.evaluate("""() => [...document.images].map(i => {
                    const box=i.getBoundingClientRect(), fit=getComputedStyle(i).objectFit;
                    const ratios=[box.width/i.naturalWidth, box.height/i.naturalHeight];
                    return {path:new URL(i.currentSrc).pathname, natural:[i.naturalWidth,i.naturalHeight], box:[Math.round(box.width),Math.round(box.height)], scale:fit==='contain'?Math.min(...ratios):Math.max(...ratios), fit, decorative:!i.alt, loading:i.loading};
                })""")
                results.append(checks)
                capture = args.screenshots == 'all' or (args.screenshots == 'representative' and (width, route) in LAUNCH_SHOTS)
                if capture:
                    page.screenshot(path=str(args.output / f"{route.replace('/', '-') or 'home'}-{width}.png"), full_page=True)
                    page.screenshot(path=str(args.output / f"{route.replace('/', '-') or 'home'}-{width}-cover.png"))
            page.close()
            print(f"Reviewed {len(routes)} routes at {width}px", flush=True)
        browser.close()
    if server:
        server.shutdown()
    (args.output / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    problems = [r for r in results if r["overflow"] or r["expandedOverflow"] or r["overlappingSeasonCaption"] or r["overlappingFieldCaption"] or r["brokenImages"] or r["missingAlt"] or r["synthetic"] or r["debugState"] or r["status"] != 200 or r["failedInternal"] or r["scriptErrors"] or not r["mobileMenu"] or r["h1"] != 1 or r["distortedTeamImages"] or r["escapedTeamImages"] or r["missingPageAnchors"] or r["unreadableLiveCards"]]
    print(json.dumps({"checks": len(results), "problems": problems}, indent=2))
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
