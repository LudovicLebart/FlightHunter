from __future__ import annotations

import datetime
import html
import json

import config
from models import Offer
from providers.base import Provider

# Sélecteurs vérifiés le 2026-07-28 contre le DOM réel (inspect_site.py,
# exécuté dans un Codespace) — voir scraper/output/debug/inspect_transat.html.
COOKIE_ACCEPT_SELECTOR = "#onetrust-accept-btn-handler"
ORIGIN_INPUT_SELECTOR = "input[aria-label='De']"
DATE_INPUT_SELECTOR = "input[aria-label='Date']"
# La page liste déjà "Toutes les destinations" du Sud par défaut — inutile
# d'interagir avec le champ "vers", une recherche couvre plusieurs
# destinations en une fois (~15 hôtels avec prix, dates, formule repas).
RESULTS_CONTAINER_SELECTOR = ".mapView[gtm-package-list]"

# Codes vus dans les données réelles du widget pour "tout inclus".
ALL_INCLUSIVE_MEAL_CODES = {"AI", "FCTC"}


class TransatProvider(Provider):
    """Air Transat (vacances Sud tout compris) — www.transat.com.

    Contrairement à une recherche classique par destination, ce widget
    affiche déjà plusieurs destinations par recherche. On ne relance donc
    une vraie navigation qu'une fois par instance de provider (mise en
    cache), et `search_one` filtre ensuite les offres déjà récupérées par
    destination/date — voir `_fetch_packages`.
    """

    name = "transat"
    base_url = "https://www.transat.com/fr-CA/voyage-pas-cher/sud"

    def __init__(self, page, debug: bool = False):
        super().__init__(page, debug)
        self._packages_cache: list[dict] | None = None

    def search_one(
        self,
        destination: "config.Destination",
        departure_date: datetime.date,
        nights_min: int,
        nights_max: int,
        pax: int,
    ) -> list[Offer]:
        if self._packages_cache is None:
            self._packages_cache = self._fetch_packages()

        offers: list[Offer] = []
        for entry in self._packages_cache:
            offer = self._package_to_offer(entry, destination, nights_min, nights_max)
            if offer is not None and offer.departure_date == departure_date:
                offers.append(offer)
        return offers

    # --- Une seule vraie navigation par run ------------------------------

    def _fetch_packages(self) -> list[dict]:
        self.goto(self.base_url)

        if self.detect_block_or_captcha():
            self.logger.warning("Blocage/captcha détecté sur Transat, on abandonne ce provider.")
            if self.debug:
                self.dump_debug("blocked_home")
            return []

        self._dismiss_cookies()
        self._select_origin()
        self._select_near_term_dates()
        self.page.wait_for_timeout(3000)  # laisse l'appel AJAX de résultats se terminer

        packages = self._extract_packages()
        self.logger.info("Transat: %d forfait(s) récupéré(s) en une recherche", len(packages))
        return packages

    def _dismiss_cookies(self) -> None:
        # La bannière OneTrust apparaît avec un léger délai après le
        # chargement (pas immédiatement) : un simple `.count()` juste après
        # `goto()` la rate souvent, laissant son overlay bloquer les clics
        # suivants sur le formulaire. On attend explicitement sa visibilité.
        try:
            btn = self.page.locator(COOKIE_ACCEPT_SELECTOR)
            btn.first.wait_for(state="visible", timeout=8000)
            btn.first.click(timeout=5000)
            self.page.wait_for_timeout(500)
        except Exception:
            self.logger.debug("Pas de bannière de cookies à fermer (ou sélecteur obsolète)")

    def _select_origin(self) -> None:
        try:
            origin_field = self.page.locator(ORIGIN_INPUT_SELECTOR)
            origin_field.first.click(timeout=5000)
            self.page.wait_for_timeout(500)
            item = self.page.locator(f"li[data-uid='{config.ORIGIN}']")
            item.first.click(timeout=5000)
        except Exception:
            self.logger.warning(
                "Impossible de sélectionner l'origine %s sur Transat (sélecteur à vérifier, "
                "on continue avec l'origine par défaut du site)",
                config.ORIGIN,
            )
            if self.debug:
                self.dump_debug("origin_select_fail")

    def _select_near_term_dates(self) -> None:
        # Les options du filtre "Date" (mois disponibles, fenêtres "< N
        # jours"...) dépendent de l'inventaire pour l'origine choisie —
        # constaté : "Days-1-7" existe pour certaines origines mais pas pour
        # Montréal, où seuls des mois (ex. "Août") étaient proposés. On
        # cherche donc dynamiquement la plus petite fenêtre "< N jours"
        # disponible plutôt que de viser une valeur fixe.
        try:
            date_field = self.page.locator(DATE_INPUT_SELECTOR)
            date_field.first.click(timeout=5000)
            self.page.wait_for_timeout(500)

            day_window_items = self.page.locator("li[data-uid^='Days-1-']")
            count = day_window_items.count()
            if count == 0:
                self.logger.info(
                    "Aucune fenêtre '< N jours' disponible pour cette origine sur Transat "
                    "(seuls des mois sont proposés) — probablement pas d'inventaire pour un "
                    "départ dans les prochains jours."
                )
                return

            best_uid, best_days = None, None
            for i in range(count):
                uid = day_window_items.nth(i).get_attribute("data-uid") or ""
                try:
                    days = int(uid.rsplit("-", 1)[-1])
                except ValueError:
                    continue
                if best_days is None or days < best_days:
                    best_uid, best_days = uid, days

            if best_uid is None:
                return

            self.page.locator(f"li[data-uid='{best_uid}']").first.click(timeout=5000)
        except Exception:
            self.logger.warning(
                "Impossible de sélectionner le filtre de dates sur Transat (sélecteur à "
                "vérifier, on continue sans filtre de date)"
            )
            if self.debug:
                self.dump_debug("date_select_fail")

    def _extract_packages(self) -> list[dict]:
        try:
            container = self.page.locator(RESULTS_CONTAINER_SELECTOR)
            if container.count() == 0:
                raise ValueError("conteneur de résultats introuvable")
            raw = container.first.get_attribute("gtm-package-list")
        except Exception:
            raw = None

        if not raw:
            self.logger.warning("gtm-package-list introuvable — structure de page changée ?")
            if self.debug:
                self.dump_debug("no_gtm_package_list")
            return []

        try:
            return json.loads(html.unescape(raw))
        except json.JSONDecodeError:
            self.logger.exception("Échec du parsing JSON de gtm-package-list")
            if self.debug:
                self.dump_debug("bad_gtm_package_list_json")
            return []

    # --- Conversion JSON -> Offer ----------------------------------------

    def _package_to_offer(
        self,
        entry: dict,
        destination: "config.Destination",
        nights_min: int,
        nights_max: int,
    ) -> Offer | None:
        pkg = entry.get("package") or {}

        if pkg.get("mealPlanCode") not in ALL_INCLUSIVE_MEAL_CODES:
            return None
        if pkg.get("destinationAirportCode") != destination.code:
            return None

        nights = pkg.get("tripDuration")
        if nights is None or not (nights_min <= nights <= nights_max):
            return None

        departure_raw = pkg.get("departureDate")
        if not departure_raw:
            return None
        try:
            departure_date = datetime.datetime.fromisoformat(departure_raw).date()
        except ValueError:
            return None

        return_raw = pkg.get("returnDate")
        return_date = (
            datetime.datetime.fromisoformat(return_raw).date()
            if return_raw
            else departure_date + datetime.timedelta(days=nights)
        )

        price_per_adult = pkg.get("totalPricePerAdult")
        if price_per_adult is None:
            return None

        booking_url = pkg.get("bookingUrl") or entry.get("url") or self.page.url
        if booking_url.startswith("/"):
            booking_url = f"https://www.transat.com{booking_url}"

        return Offer(
            provider=self.name,
            destination_code=destination.code,
            destination_name=destination.name,
            departure_date=departure_date,
            return_date=return_date,
            nights=nights,
            price_total_cad=float(price_per_adult) * config.PAX,
            hotel_name=entry.get("name") or "Hôtel inconnu",
            board_type="all_inclusive",
            sargassum_risk=destination.sargassum_risk,
            url=booking_url,
            scraped_at=datetime.datetime.now(),
        )
