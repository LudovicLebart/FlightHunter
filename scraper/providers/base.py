from __future__ import annotations

import datetime
import logging
import os
import random
import time
from abc import ABC, abstractmethod

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

import config
from models import Offer


class ProviderError(Exception):
    """Raised when a provider search fails in a way we can't recover from."""


class Provider(ABC):
    """Interface commune à tous les voyagistes scrapés.

    Chaque provider concret doit implémenter `search_one`, qui exécute UNE
    recherche (une destination + une date de départ + une plage de nuits) et
    retourne la liste des offres trouvées sur la page de résultats.

    Toute la logique de sélecteurs CSS/XPath spécifique à un site vit dans le
    provider concret — c'est la partie la plus susceptible de casser si le
    site change son DOM, donc elle est volontairement isolée ici.
    """

    name: str = "base"
    base_url: str = ""

    def __init__(self, page: Page, debug: bool = False):
        self.page = page
        self.debug = debug
        self.logger = logging.getLogger(f"scraper.{self.name}")

    @abstractmethod
    def search_one(
        self,
        destination: "config.Destination",
        departure_date: datetime.date,
        nights_min: int,
        nights_max: int,
        pax: int,
    ) -> list[Offer]:
        """Exécute une recherche et retourne les offres trouvées (liste vide si aucune)."""
        raise NotImplementedError

    # --- Helpers communs ---------------------------------------------------

    def polite_delay(self) -> None:
        low, high = config.REQUEST_DELAY_SECONDS
        time.sleep(random.uniform(low, high))

    def goto(self, url: str) -> None:
        last_error: Exception | None = None
        for attempt in range(1, config.NAV_RETRIES + 2):
            try:
                self.page.goto(url, timeout=config.PAGE_TIMEOUT_MS, wait_until="domcontentloaded")
                return
            except PlaywrightTimeoutError as exc:
                last_error = exc
                self.logger.warning(
                    "Timeout en chargeant %s (tentative %d/%d)", url, attempt, config.NAV_RETRIES + 1
                )
        raise ProviderError(f"Échec de navigation vers {url}") from last_error

    def dump_debug(self, tag: str) -> None:
        """Sauvegarde une capture d'écran + le HTML de la page courante pour debug."""
        os.makedirs(config.DEBUG_DIR, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.join(config.DEBUG_DIR, f"{self.name}_{tag}_{ts}")
        try:
            self.page.screenshot(path=f"{base}.png", full_page=True)
        except Exception:
            self.logger.exception("Impossible de sauvegarder la capture d'écran de debug")
        try:
            with open(f"{base}.html", "w", encoding="utf-8") as f:
                f.write(self.page.content())
        except Exception:
            self.logger.exception("Impossible de sauvegarder le HTML de debug")
        self.logger.info("Debug sauvegardé: %s.png / %s.html", base, base)

    def first_matching(self, selectors: list[str], root=None):
        """Essaie plusieurs sélecteurs candidats (le DOM des sites change souvent)
        et retourne le premier Locator qui matche au moins un élément, ou None."""
        scope = root if root is not None else self.page
        for sel in selectors:
            loc = scope.locator(sel)
            try:
                if loc.count() > 0:
                    return loc
            except Exception:
                continue
        return None

    def detect_block_or_captcha(self) -> bool:
        """Heuristique simple pour repérer un blocage/captcha et abandonner proprement
        plutôt que d'insister (voir section Éthique du README)."""
        try:
            content = self.page.content().lower()
        except Exception:
            return False
        markers = [
            "captcha",
            "are you a robot",
            "unusual traffic",
            "access denied",
            "request blocked",
            "pardon our interruption",
        ]
        return any(m in content for m in markers)
