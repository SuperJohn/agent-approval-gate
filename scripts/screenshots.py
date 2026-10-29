"""Capture README screenshots of the static replay. Not part of CI."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images"
URL = "http://127.0.0.1:8099/"


def main() -> None:
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8099", "--directory", str(ROOT / "site")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(0.5)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path="/usr/local/bin/google-chrome",
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.goto(URL + "?theme=light#refund-stalled", wait_until="domcontentloaded")
            page.wait_for_selector("#btn-approve")
            page.screenshot(path=str(OUT / "pending-approval.png"))

            page.click("#btn-approve")
            page.wait_for_selector("[data-event='decision.replayed']")
            page.screenshot(path=str(OUT / "approved-resume.png"), full_page=True)

            page.goto(URL + "?theme=dark#email-vendor", wait_until="domcontentloaded")
            page.wait_for_selector("#btn-deny")
            page.click("#btn-deny")
            page.wait_for_selector("[data-event='decision.denied']")
            page.screenshot(path=str(OUT / "denied-dark.png"), full_page=True)

            page.goto(URL + "?theme=light#refund-goodwill", wait_until="domcontentloaded")
            page.wait_for_selector("#btn-edit")
            page.click("#btn-edit")
            page.wait_for_selector("#btn-apply-edit")
            page.click("#btn-apply-edit")
            page.wait_for_selector("[data-event='tool.executed']")
            page.screenshot(path=str(OUT / "edited-refund.png"), full_page=True)
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    main()
