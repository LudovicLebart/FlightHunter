from __future__ import annotations

import datetime
import re

import config
from models import Offer
from providers.base import Provider, ProviderError

FRENCH_MONTHS = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
    7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre",
}

# Sélecteurs vérifiés le 2026-07-28 contre le DOM réel du formulaire de
# recherche (inspect_site.py) — voir
# scraper/output/debug/inspect_air_canada_vacations.html. Les champs
# origine/destination sont de vrais comboboxes texte (taper puis cliquer une
# suggestion). Le calendrier de dates (vue-datepicker) N'A PAS pu être
# vérifié en interaction réelle (clic + navigation de mois) — c'est du
# best-effort, à corriger après un prochain dump de debug si ça échoue.
COOKIE_ACCEPT_SELECTORS = [
    "button:has-text('Accepter tout')",
    "#onetrust-accept-btn-handler",
]
ORIGIN_INPUT_SELECTOR = "#vacation_packages_tab-from-input"
ORIGIN_LISTBOX_SELECTOR = "#vacation_packages_tab-from-listbox li"
DESTINATION_INPUT_SELECTOR = "#vacation_packages_tab-to-input"
DESTINATION_LISTBOX_SELECTOR = "#vacation_packages_tab-to-listbox li"
DEPARTURE_DATE_INPUT_SELECTOR = "#vacation_packages_tab-departureDateId"
# ATTENTION : la classe "vacv-btn-primary" est aussi utilisée par le bouton
# "Se connecter" (Aeroplan) — un simple `button.vacv-btn-primary` matche les
# deux et `.first` peut résoudre sur le mauvais bouton. Il faut filtrer sur
# le texte "Rechercher".
SEARCH_BUTTON_SELECTOR = "button.vacv-btn-primary:has-text('Rechercher')"

# Sélecteurs de la page de résultats — NON VÉRIFIÉS (jamais observés en
# conditions réelles, cette page n'a pas encore été atteinte). Suppositions
# raisonnables à corriger via un dump de debug une fois qu'une recherche
# aboutit.
RESULT_CARD_SELECTORS = [
    "[data-testid='package-card']",
    ".package-result-card",
    "li.result-item",
]
HOTEL_NAME_SELECTORS = ["[data-testid='hotel-name']", ".hotel-name", "h3"]
PRICE_SELECTORS = ["[data-testid='price']", ".price-total", ".price"]
BOARD_TYPE_SELECTORS = ["[data-testid='board-type']", ".board-type", ".meal-plan"]
NIGHTS_SELECTORS = ["[data-testid='nights']", ".nights", ".duration"]
LINK_SELECTORS = ["a"]


class AirCanadaVacationsProvider(Provider):
    """Vacances Air Canada — vacations.aircanada.com/fr.

    Formulaire de recherche vérifié contre le DOM réel. La sélection de
    dates (calendrier vue-datepicker) et le parsing de la page de résultats
    restent best-effort — voir README.md.
    """

    name = "air_canada_vacations"
    base_url = "https://vacations.aircanada.com/fr"

    def search_one(
        self,
        destination: "config.Destination",
        departure_date: datetime.date,
        nights_min: int,
        nights_max: int,
        pax: int,
    ) -> list[Offer]:
        offers: list[Offer] = []

        self.goto(self.base_url)

        if self.detect_block_or_captcha():
            self.logger.warning("Blocage/captcha détecté sur Vacances Air Canada, on saute.")
            if self.debug:
                self.dump_debug("blocked_home")
            return offers

        self._dismiss_cookies()

        try:
            self._fill_search_form(destination, departure_date, nights_min, nights_max)
        except ProviderError:
            self.logger.warning(
                "Impossible de remplir le formulaire pour %s le %s (sélecteur à vérifier)",
                destination.code,
                departure_date,
            )
            if self.debug:
                self.dump_debug(f"form_fail_{destination.code}_{departure_date}")
            return offers

        # La page de résultats n'a jamais été observée : on dump toujours en
        # debug pour pouvoir finaliser les sélecteurs au prochain passage.
        if self.debug:
            self.dump_debug(f"results_{destination.code}_{departure_date}")

        try:
            self.page.wait_for_selector(", ".join(RESULT_CARD_SELECTORS), timeout=config.PAGE_TIMEOUT_MS)
        except Exception:
            self.logger.info(
                "Aucun résultat (ou sélecteur de carte à corriger) pour %s le %s.",
                destination.code,
                departure_date,
            )
            return offers

        return self._parse_results(destination, departure_date, nights_max)

    # --- Formulaire (vérifié) --------------------------------------------

    def _dismiss_cookies(self) -> None:
        # La bannière peut apparaître avec un léger délai après le
        # chargement : on attend sa visibilité plutôt que de vérifier tout
        # de suite, sinon son overlay peut bloquer les clics suivants.
        for sel in COOKIE_ACCEPT_SELECTORS:
            try:
                btn = self.page.locator(sel)
                btn.first.wait_for(state="visible", timeout=4000)
                btn.first.click(timeout=5000)
                self.page.wait_for_timeout(500)
                return
            except Exception:
                continue

    def _fill_combobox(self, input_selector: str, listbox_item_selector: str, query: str) -> None:
        field = self.page.locator(input_selector)
        field.first.click(timeout=5000)
        field.first.fill("")
        # `.fill()` seul ne déclenche pas toujours les événements attendus
        # par l'autocomplete (constaté : "Aucun résultat trouvé" même pour
        # un code d'aéroport valide) — on tape caractère par caractère comme
        # un vrai clavier.
        field.first.press_sequentially(query, delay=80)
        self.page.wait_for_timeout(1200)  # laisse l'autocomplete se peupler
        items = self.page.locator(listbox_item_selector)
        if items.count() == 0 or "aucun résultat" in (items.first.inner_text() or "").lower():
            raise ProviderError(f"Aucune suggestion pour {query!r} sur {input_selector}")

        # Un clic souris direct sur le <li> ne suffit pas toujours à faire
        # "prendre" la sélection (constaté : le champ restait vide après
        # clic, avec `value=""` dans le DOM) — la navigation clavier
        # (flèche bas + Entrée) déclenche plus fiablement le handler de
        # sélection de ce type de combobox. On retombe sur le clic souris
        # si le clavier n'a pas fonctionné non plus.
        field.first.press("ArrowDown")
        self.page.wait_for_timeout(200)
        field.first.press("Enter")
        self.page.wait_for_timeout(300)
        if not field.first.input_value():
            items.first.click(timeout=5000)
            self.page.wait_for_timeout(300)
        if not field.first.input_value():
            raise ProviderError(f"La sélection de {query!r} sur {input_selector} n'a pas pris (champ vide)")

    def _fill_search_form(
        self,
        destination: "config.Destination",
        departure_date: datetime.date,
        nights_min: int,
        nights_max: int,
    ) -> None:
        try:
            self._fill_combobox(ORIGIN_INPUT_SELECTOR, ORIGIN_LISTBOX_SELECTOR, config.ORIGIN)
            self._fill_combobox(DESTINATION_INPUT_SELECTOR, DESTINATION_LISTBOX_SELECTOR, destination.name)
        except ProviderError:
            raise

        self._select_dates_best_effort(departure_date, nights_min, nights_max)

        # Voyageurs : laissé par défaut ("2 voyageurs - 1 chambre"), cohérent
        # avec config.PAX=2 par défaut. À ajuster manuellement dans le code
        # si PAX change et que le défaut du site ne correspond plus.

        search_button = self.page.locator(SEARCH_BUTTON_SELECTOR)
        if search_button.count() == 0:
            raise ProviderError("Bouton de recherche introuvable")
        search_button.first.click(timeout=5000)
        self.page.wait_for_timeout(2000)

    def _select_dates_best_effort(
        self, departure_date: datetime.date, nights_min: int, nights_max: int
    ) -> None:
        """Best-effort : ouvre le calendrier (vue-datepicker) et tente de
        cliquer le jour de départ puis un jour de retour. Non vérifié en
        conditions réelles — enveloppé pour ne jamais faire planter le run.
        """
        try:
            date_field = self.page.locator(DEPARTURE_DATE_INPUT_SELECTOR)
            date_field.first.click(timeout=5000)
            self.page.wait_for_timeout(500)

            mid_nights = (nights_min + nights_max) // 2
            return_date = departure_date + datetime.timedelta(days=mid_nights)

            self._navigate_calendar_to_month(departure_date)
            self._click_calendar_day(departure_date)
            self.page.wait_for_timeout(500)
            self._navigate_calendar_to_month(return_date)
            self._click_calendar_day(return_date)
        except Exception:
            self.logger.warning(
                "Sélection de dates non confirmée sur le calendrier (best-effort, "
                "sélecteurs à vérifier) — la recherche continue avec les dates par défaut."
            )
            if self.debug:
                self.dump_debug("calendar_select_fail")

    def _navigate_calendar_to_month(self, target: datetime.date) -> None:
        # vue-datepicker : en-tête du mois affiché dans ".dp__month_year_wrap",
        # bouton "mois suivant" généralement le dernier ".dp__inner_nav".
        # Nos dates cibles (août) sont dans un mois différent du mois
        # courant (juillet) — sans cette navigation, le clic sur le jour
        # tomberait sur le mauvais mois. Non vérifié en conditions réelles.
        target_label = f"{FRENCH_MONTHS[target.month]} {target.year}"
        header = self.page.locator(".dp__month_year_wrap")
        next_btn = self.page.locator("button.dp__inner_nav").last
        if header.count() == 0 or next_btn.count() == 0:
            return
        for _ in range(8):  # garde-fou pour ne jamais boucler indéfiniment
            current = (header.first.inner_text() or "").strip().lower()
            if target_label in current:
                return
            next_btn.click(timeout=3000)
            self.page.wait_for_timeout(300)

    def _click_calendar_day(self, day: datetime.date) -> None:
        # vue-datepicker : chaque case de jour est un ".dp__cell_inner".
        # Le mois affiché par défaut n'est pas garanti être le bon —
        # tentative simple sans navigation de mois pour l'instant.
        cells = self.page.locator(".dp__cell_inner:not(.dp__cell_disabled)")
        target_text = str(day.day)
        count = cells.count()
        for i in range(count):
            cell = cells.nth(i)
            if cell.inner_text().strip() == target_text:
                cell.click(timeout=3000)
                return
        raise ProviderError(f"Case du calendrier introuvable pour le {day}")

    # --- Résultats (non vérifié) ------------------------------------------

    def _parse_results(
        self,
        destination: "config.Destination",
        departure_date: datetime.date,
        default_nights: int,
    ) -> list[Offer]:
        offers: list[Offer] = []
        cards = self.first_matching(RESULT_CARD_SELECTORS)
        if not cards:
            return offers

        count = min(cards.count(), 20)
        for i in range(count):
            card = cards.nth(i)
            try:
                hotel_name = self._extract_text(card, HOTEL_NAME_SELECTORS) or "Hôtel inconnu"
                price = self._parse_price(self._extract_text(card, PRICE_SELECTORS))
                if price is None:
                    continue

                board_text = (self._extract_text(card, BOARD_TYPE_SELECTORS) or "").lower()
                if board_text and "tout compris" not in board_text and "all inclusive" not in board_text:
                    continue

                nights = self._parse_nights(self._extract_text(card, NIGHTS_SELECTORS)) or default_nights

                link_el = self.first_matching(LINK_SELECTORS, root=card)
                url = link_el.first.get_attribute("href") if link_el else self.page.url
                if url and url.startswith("/"):
                    url = f"{self.base_url.rstrip('/')}{url}"

                offers.append(
                    Offer(
                        provider=self.name,
                        destination_code=destination.code,
                        destination_name=destination.name,
                        departure_date=departure_date,
                        return_date=departure_date + datetime.timedelta(days=nights),
                        nights=nights,
                        price_total_cad=price,
                        hotel_name=hotel_name.strip(),
                        board_type="all_inclusive",
                        sargassum_risk=destination.sargassum_risk,
                        url=url or self.page.url,
                        scraped_at=datetime.datetime.now(),
                    )
                )
            except Exception:
                self.logger.exception("Erreur en parsant une carte de résultat (ignorée)")
                continue

        return offers

    def _extract_text(self, root, selectors: list[str]) -> str | None:
        loc = self.first_matching(selectors, root=root)
        if not loc:
            return None
        try:
            return loc.first.inner_text()
        except Exception:
            return None

    @staticmethod
    def _parse_price(text: str | None) -> float | None:
        if not text:
            return None
        match = re.search(r"[\d\s.,]+", text.replace("\xa0", " "))
        if not match:
            return None
        raw = match.group(0).strip()
        decimal_match = re.search(r"[.,](\d{1,2})$", raw)
        if decimal_match:
            integer_part = re.sub(r"\D", "", raw[: decimal_match.start()])
            decimal_part = decimal_match.group(1)
            digits = f"{integer_part}.{decimal_part}" if integer_part else f"0.{decimal_part}"
        else:
            digits = re.sub(r"\D", "", raw)
        try:
            return float(digits) if digits else None
        except ValueError:
            return None

    @staticmethod
    def _parse_nights(text: str | None) -> int | None:
        if not text:
            return None
        match = re.search(r"(\d+)\s*nuit", text.lower())
        return int(match.group(1)) if match else None
