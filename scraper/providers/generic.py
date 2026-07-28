from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field

import config
from models import Offer
from providers.base import Provider, ProviderError


@dataclass
class Selectors:
    """Sélecteurs candidats pour un voyagiste donné.

    Chaque champ est une liste essayée dans l'ordre (voir
    `Provider.first_matching`). Ce sont des suppositions raisonnables
    (attributs `data-testid`, noms de champs usuels...) — À VÉRIFIER contre
    le site réel au premier run avec --debug (voir README.md).
    """

    origin_input: list[str]
    destination_input: list[str]
    departure_date: list[str]
    return_date: list[str]
    nights_min: list[str]
    nights_max: list[str]
    pax_input: list[str]
    search_button: list[str]
    result_card: list[str]
    hotel_name: list[str]
    price: list[str]
    board_type: list[str]
    nights: list[str]
    link: list[str] = field(default_factory=lambda: ["a"])


class GenericPackageProvider(Provider):
    """Logique de recherche/scraping partagée entre voyagistes de forfaits
    tout-inclus dont l'UI de recherche suit le schéma classique : formulaire
    origine/destination/dates/nuits/passagers -> liste de cartes résultat.

    Un provider concret n'a besoin de définir que `name`, `base_url` et
    `selectors` (voir transat.py / air_canada_vacations.py pour un exemple).
    """

    base_url: str = ""
    selectors: Selectors

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
            self.logger.warning("Blocage/captcha détecté sur la page d'accueil, on saute.")
            if self.debug:
                self.dump_debug("blocked_home")
            return offers

        try:
            self._fill_search_form(destination, departure_date, nights_min, nights_max, pax)
        except ProviderError:
            self.logger.warning(
                "Impossible de remplir le formulaire pour %s le %s — sélecteurs à vérifier.",
                destination.code,
                departure_date,
            )
            if self.debug:
                self.dump_debug(f"form_fail_{destination.code}_{departure_date}")
            return offers

        try:
            self.page.wait_for_selector(
                ", ".join(self.selectors.result_card), timeout=config.PAGE_TIMEOUT_MS
            )
        except Exception:
            self.logger.info(
                "Aucun résultat (ou timeout) pour %s le %s.", destination.code, departure_date
            )
            if self.debug:
                self.dump_debug(f"no_results_{destination.code}_{departure_date}")
            return offers

        return self._parse_results(destination, departure_date, nights_max)

    # --- Étapes internes -----------------------------------------------

    def _fill_search_form(
        self,
        destination: "config.Destination",
        departure_date: datetime.date,
        nights_min: int,
        nights_max: int,
        pax: int,
    ) -> None:
        sel = self.selectors
        origin_field = self.first_matching(sel.origin_input)
        destination_field = self.first_matching(sel.destination_input)
        departure_field = self.first_matching(sel.departure_date)
        search_button = self.first_matching(sel.search_button)

        if not all([origin_field, destination_field, departure_field, search_button]):
            raise ProviderError("Formulaire de recherche introuvable (sélecteurs à mettre à jour)")

        origin_field.first.fill(config.ORIGIN)
        destination_field.first.fill(f"{destination.name}, {destination.country}")
        departure_field.first.fill(departure_date.strftime("%Y-%m-%d"))

        nights_min_field = self.first_matching(sel.nights_min)
        nights_max_field = self.first_matching(sel.nights_max)
        if nights_min_field and nights_max_field:
            nights_min_field.first.fill(str(nights_min))
            nights_max_field.first.fill(str(nights_max))
        else:
            mid_nights = (nights_min + nights_max) // 2
            return_field = self.first_matching(sel.return_date)
            if return_field:
                return_date = departure_date + datetime.timedelta(days=mid_nights)
                return_field.first.fill(return_date.strftime("%Y-%m-%d"))

        pax_field = self.first_matching(sel.pax_input)
        if pax_field:
            pax_field.first.fill(str(pax))

        search_button.first.click()
        self.polite_delay()

    def _parse_results(
        self,
        destination: "config.Destination",
        departure_date: datetime.date,
        default_nights: int,
    ) -> list[Offer]:
        sel = self.selectors
        offers: list[Offer] = []
        cards = self.first_matching(sel.result_card)
        if not cards:
            return offers

        count = min(cards.count(), 20)  # on plafonne pour rester raisonnable
        for i in range(count):
            card = cards.nth(i)
            try:
                hotel_name = self._extract_text(card, sel.hotel_name) or "Hôtel inconnu"
                price = self._parse_price(self._extract_text(card, sel.price))
                if price is None:
                    continue

                board_text = (self._extract_text(card, sel.board_type) or "").lower()
                if board_text and "tout compris" not in board_text and "all inclusive" not in board_text:
                    continue

                nights = self._parse_nights(self._extract_text(card, sel.nights)) or default_nights

                link_el = self.first_matching(sel.link, root=card)
                url = link_el.first.get_attribute("href") if link_el else self.page.url
                if url and url.startswith("/"):
                    url = self.base_url.rstrip("/") + url

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
        """Gère les deux formats courants :
        - fr-CA : "4 200,00 $" (espace = milliers, virgule = décimales)
        - en    : "$4,200.00" (virgule = milliers, point = décimales)
        """
        if not text:
            return None
        match = re.search(r"[\d\s.,]+", text.replace("\xa0", " "))
        if not match:
            return None
        raw = match.group(0).strip()

        # Séparateur décimal = dernier , ou . suivi de 1 ou 2 chiffres en fin de nombre.
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
