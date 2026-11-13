import os
from playwright.sync_api import sync_playwright

SITE = "https://zefame.com/free-facebook-followers"
FACEBOOK_URL = os.getenv("FACEBOOK_URL", "https://www.facebook.com/share/1AGzhdTkSf/?mibextid=wwXIfr")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        response = page.goto(SITE, wait_until="domcontentloaded", timeout=30000)
        print("HTTP:", response.status if response else "inconnu")
        if "temporairement indisponible" in page.locator("body").inner_text().lower():
            print("Service indisponible")
        else:
            fields = page.locator('input[type="url"], input[type="text"]')
            if fields.count():
                fields.first.fill(FACEBOOK_URL)
                print("Lien inséré pour vérification, sans envoi")
            else:
                print("Champ introuvable")
        page.screenshot(path="resultat.png", full_page=True)
    finally:
        browser.close()
