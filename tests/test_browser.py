"""Runs against real Chromium when installed; otherwise reports explicit skips."""
from pathlib import Path
import shutil
import tempfile
import threading
import unittest

from driod.browser_worker import check
from driod.tools import Toolbox
from driod.workspace import Workspace


class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
        except Exception as exc:
            raise unittest.SkipTest("Chromium unavailable: run setup_browser.bat. " + str(exc)[:100])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.ws = Workspace(base / "project", base / "state")
        source = Path(__file__).resolve().parents[1] / "examples" / "store"
        shutil.copytree(source, self.ws.root / "store")
        self.box = Toolbox(self.ws, lambda *args: True, lambda *args: None, threading.Event())
        self.url = self.box.start_preview("store")["url"]

    def tearDown(self):
        self.box.close()
        self.temp.cleanup()

    def test_search_cart_and_demo_checkout(self):
        steps = [
            {"action": "assert_count", "selector": ".product", "value": "8"},
            {"action": "fill", "selector": "#search", "value": "Headphones"},
            {"action": "assert_count", "selector": ".product", "value": "1"},
            {"action": "click", "selector": "[data-add='1']"},
            {"action": "assert_text", "selector": "#cart-count", "value": "1"},
            {"action": "click", "selector": "#cart-open"},
            {"action": "assert_text", "selector": "#cart-total", "value": "2,499"},
            {"action": "click", "selector": "#checkout"},
            {"action": "assert_text", "selector": "#checkout-note", "value": "no order was placed"},
        ]
        result = check({"url": self.url, "steps": steps, "screenshot": str(self.ws.root / "desktop.png")})
        self.assertTrue(result["passed"], result)
        mobile = check({"url": self.url, "width": 390, "screenshot": str(self.ws.root / "mobile.png")})
        self.assertTrue(mobile["passed"], mobile)

    def test_detect_javascript_error_then_repair(self):
        js = self.ws.read_file("store/app.js")["content"]
        self.ws.write_file("store/app.js", js + "\nmissingFunctionForTest();")
        config = {"url": self.url, "screenshot": str(self.ws.root / "error.png")}
        broken = check(config)
        self.assertFalse(broken["passed"])
        self.assertTrue(any("missingFunctionForTest" in x for x in broken["errors"]))
        self.ws.write_file("store/app.js", js)
        repaired = check(config)
        self.assertTrue(repaired["passed"], repaired)


if __name__ == "__main__":
    unittest.main(verbosity=2)
