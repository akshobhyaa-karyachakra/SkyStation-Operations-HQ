from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = 'http://127.0.0.1:8892/public-wallboard.html?cycle=0'
BROWSER = '/opt/data/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome'
TARGETS = [(1920, 1080), (1366, 768), (390, 844)]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=BROWSER)
    for width, height in TARGETS:
        page = browser.new_page(viewport={'width': width, 'height': height})
        errors = []
        page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
        page.goto(URL, wait_until='networkidle')
        page.wait_for_timeout(700)
        box = page.locator('.tv').bounding_box()
        body = page.locator('body').evaluate('(e) => ({ width: e.scrollWidth, height: e.scrollHeight })')
        assert box and box['x'] >= -1 and box['y'] >= -1
        assert box['x'] + box['width'] <= width + 1
        if width >= 900:
            assert box['y'] + box['height'] <= height + 1
            assert body['width'] <= width
        page.screenshot(path=f'/tmp/wallboard-{width}x{height}.png')
        for _ in range(5):
            page.keyboard.press('ArrowRight')
            page.wait_for_timeout(420)
            assert page.locator('.tv').count() == 1
        assert not errors, errors
        print({'viewport': (width, height), 'stage': box, 'body': body, 'screens_checked': 6})
        page.close()
    browser.close()
