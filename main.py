"""Vérification du formulaire gratuit : aucune commande n'est soumise."""
import json
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright

SITE = "https://zefame.com/free-facebook-followers"
FACEBOOK_URL = os.getenv("FACEBOOK_URL", "https://www.facebook.com/share/1AGzhdTkSf/?mibextid=wwXIfr")
OUT = Path("resultats")


def main():
    OUT.mkdir(exist_ok=True)
    report = {
        "date_paris": datetime.now(ZoneInfo("Europe/Paris")).isoformat(),
        "statut": "erreur", "lien_rempli": False, "soumission": False,
        "motif": "Aucune méthode autorisée documentée pour automatiser l'offre gratuite.",
        "avertissement": "Zefame demande un profil public direct ; le lien fourni est un lien de partage.",
    }
    exit_code = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(locale="fr-FR")
        page.set_default_timeout(15000)
        try:
            response = page.goto(SITE, wait_until="networkidle", timeout=45000)
            report["http"] = response.status if response else None
            report["url_finale"] = page.url
            text = page.locator("body").inner_text()
            (OUT / "page.txt").write_text(text, encoding="utf-8")
            if response and response.status >= 400:
                raise RuntimeError(f"Réponse HTTP {response.status}")
            if re.search(r"verify you are human|checking your browser|just a moment|vérifiez que vous êtes humain|unusual traffic|access denied", text, re.I):
                report["statut"] = "protection_detectee"
            elif re.search(r"temporairement indisponible|temporarily unavailable|under maintenance", text, re.I):
                report["statut"] = "indisponible"
            else:
                field = page.locator("#facebook-link")
                button = page.locator("#submit-btn")
                if field.count() != 1 or button.count() != 1:
                    raise RuntimeError("Formulaire attendu introuvable : vérifier la structure du site.")
                if not field.is_visible() or not field.is_enabled() or not button.is_enabled():
                    report["statut"] = "formulaire_indisponible"
                else:
                    field.fill(FACEBOOK_URL)
                    report["lien_rempli"] = field.input_value() == FACEBOOK_URL
                    report["statut"] = "formulaire_accessible_sans_soumission"
            # Aucun clic de soumission, appel d'API privée ou traitement de CAPTCHA.
        except Exception as exc:
            report["statut"] = "erreur"
            report["erreur"] = str(exc)
            exit_code = 1
        finally:
            try:
                page.screenshot(path=str(OUT / "capture.png"), full_page=True)
            except Exception as exc:
                report["erreur_capture"] = str(exc)
            browser.close()
    (OUT / "rapport.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    summary = "## Vérification Zefame\n\n" + "\n".join(f"- {key} : {value}" for key, value in report.items()) + "\n"
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(summary)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
