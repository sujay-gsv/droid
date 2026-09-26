"""Isolated, cancellable browser checks; input and output are JSON."""
import json
import sys
from urllib.parse import urlsplit


def check(config):
    from playwright.sync_api import sync_playwright
    errors, failed, responses, actions, blocked = [], [], [], [], []
    url = config["url"]
    origin = urlsplit(url)
    def same_origin(value):
        p = urlsplit(value)
        return (p.scheme, p.netloc) == (origin.scheme, origin.netloc)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": config.get("width", 1440), "height": 1000},
                                      service_workers="block", accept_downloads=False)
        def route(request):
            target = request.request.url
            if config.get("external", False) or same_origin(target) or target.startswith(("data:", "blob:")):
                request.continue_()
            else:
                blocked.append(target)
                request.abort()
        context.route("**/*", route)
        page = context.new_page()
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.on("requestfailed", lambda req: failed.append({"url": req.url, "error": req.failure}))
        page.on("response", lambda resp: responses.append({"url": resp.url, "status": resp.status}) if resp.status >= 400 else None)
        page.set_default_timeout(8000)
        status = None
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=25000)
            status = response.status if response else None
            page.wait_for_timeout(500)
            for step in config.get("steps", [])[:20]:
                action = step["action"]
                locator = page.locator(step.get("selector", "body"))
                if action == "click":
                    locator.click()
                elif action == "fill":
                    locator.fill(step["value"])
                elif action == "press":
                    locator.press(step["value"])
                elif action == "assert_text":
                    from playwright.sync_api import expect
                    expect(locator).to_contain_text(step["value"])
                elif action == "assert_count":
                    from playwright.sync_api import expect
                    expect(locator).to_have_count(int(step["value"]))
                else:
                    raise ValueError("Unknown browser action " + action)
                actions.append({**step, "passed": True})
        except Exception as exc:
            errors.append(str(exc)[:3000])
        title = page.title()
        body = page.locator("body").inner_text()[:14000] if page.locator("body").count() else ""
        page.screenshot(path=config["screenshot"], full_page=True, timeout=15000)
        result = {"url": page.url, "status": status, "title": title, "text": body,
                  "errors": errors[:30], "failed_requests": failed[:30], "http_errors": responses[:30],
                  "blocked_external_requests": blocked[:30], "steps": actions,
                  "screenshot": config["screenshot"],
                  "passed": status is not None and status < 400 and not errors and not responses and not failed}
        browser.close()
        return result


if __name__ == "__main__":
    try:
        print(json.dumps(check(json.load(sys.stdin))))
    except Exception as exc:
        print(json.dumps({"error": str(exc), "hint": "Run setup_browser.bat if Chromium is missing."}))
        sys.exit(1)
