#!/usr/bin/env python3
"""Login to Unicast via Playwright and save session cookies."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

COOKIES_FILE = Path("cookies.json")


def login() -> bool:
    load_dotenv()
    user = os.getenv("ULIEGE_USER")
    pwd = os.getenv("ULIEGE_PASS")
    if not user or not pwd:
        print("Erreur : ULIEGE_USER ou ULIEGE_PASS manquant dans .env")
        return False

    print("Connexion à Unicast...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/135.0"
        )
        page = ctx.new_page()
        page.goto("https://my.unicast.uliege.be/")
        page.wait_for_load_state("networkidle")

        if "idp.uliege.be" in page.url:
            page.click('a[href*="sourceChoice=ulg-ldap"]')
            page.wait_for_selector("input#login-username")
            page.fill("input#login-username", user)
            page.fill("input#login-password", pwd)
            page.press("input#login-password", "Enter")
            page.wait_for_url("https://my.unicast.uliege.be/**", timeout=30000)

        cookies = ctx.cookies()
        browser.close()

    COOKIES_FILE.write_text(json.dumps(cookies, indent=2))
    print(f"Connecté ({len(cookies)} cookies sauvegardés).")
    return True


def load_cookies() -> str | None:
    if not COOKIES_FILE.exists():
        return None
    cookies = json.loads(COOKIES_FILE.read_text())
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


if __name__ == "__main__":
    login()
