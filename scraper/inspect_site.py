"""Script ponctuel : dump le HTML + une capture d'écran des pages de recherche
des voyagistes, pour permettre de corriger les sélecteurs dans
providers/transat.py et providers/air_canada_vacations.py sans deviner.

À lancer une seule fois dans un environnement avec un vrai accès internet
(ex: Codespace) :

    python inspect_site.py

Résultats dans output/debug/inspect_<provider>.html et .png — commite-les et
pousse-les, ils seront lus pour finaliser les sélecteurs.
"""
from __future__ import annotations

import os

from playwright.sync_api import sync_playwright

import config
from providers.air_canada_vacations import AirCanadaVacationsProvider
from providers.transat import TransatProvider

TARGETS = [
    ("transat", TransatProvider.base_url),
    ("air_canada_vacations", AirCanadaVacationsProvider.base_url),
]


def main() -> None:
    os.makedirs(config.DEBUG_DIR, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="fr-CA",
            viewport={"width": 1366, "height": 900},
        )
        page = context.new_page()

        for name, url in TARGETS:
            print(f"--- {name}: {url} ---")
            try:
                page.goto(url, timeout=45000, wait_until="networkidle")
            except Exception as exc:
                print(f"  goto warning (on continue quand même): {exc}")
            page.wait_for_timeout(4000)  # laisse le temps aux widgets JS de se charger

            html_path = os.path.join(config.DEBUG_DIR, f"inspect_{name}.html")
            png_path = os.path.join(config.DEBUG_DIR, f"inspect_{name}.png")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(page.content())
            try:
                page.screenshot(path=png_path, full_page=True)
            except Exception as exc:
                print(f"  screenshot échouée: {exc}")

            print(f"  title: {page.title()!r}")
            print(f"  url finale: {page.url}")
            print(f"  -> {html_path}")
            print(f"  -> {png_path}")

        browser.close()

    print("\nTerminé. Commite et pousse le dossier output/debug/ (git add -f).")


if __name__ == "__main__":
    main()
