from __future__ import annotations

import logging

from playwright.sync_api import sync_playwright

import config
from models import Offer
from providers.air_canada_vacations import AirCanadaVacationsProvider
from providers.transat import TransatProvider

PROVIDER_CLASSES = {
    "transat": TransatProvider,
    "air_canada_vacations": AirCanadaVacationsProvider,
}

logger = logging.getLogger("scraper.brute_force")


def run_brute_force(
    provider_names: list[str] | None = None,
    debug: bool = False,
) -> list[Offer]:
    """Combine toutes les destinations actives x dates de départ pour les
    providers demandés, et retourne la liste brute des offres trouvées
    (avant tri/filtre — voir aggregate.py).
    """
    provider_names = provider_names or config.ENABLED_PROVIDERS
    destinations = config.active_destinations()
    dates = config.departure_dates()

    total_searches = len(provider_names) * len(destinations) * len(dates)
    logger.info(
        "Brute force: %d provider(s) x %d destination(s) x %d date(s) = %d recherches",
        len(provider_names),
        len(destinations),
        len(dates),
        total_searches,
    )

    all_offers: list[Offer] = []
    done = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not debug)
        try:
            for provider_name in provider_names:
                provider_cls = PROVIDER_CLASSES.get(provider_name)
                if provider_cls is None:
                    logger.warning("Provider inconnu, ignoré: %s", provider_name)
                    continue

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
                provider = provider_cls(page, debug=debug)

                for destination in destinations:
                    for departure_date in dates:
                        done += 1
                        logger.info(
                            "[%d/%d] %s: %s le %s",
                            done,
                            total_searches,
                            provider_name,
                            destination.code,
                            departure_date,
                        )
                        try:
                            offers = provider.search_one(
                                destination=destination,
                                departure_date=departure_date,
                                nights_min=config.NIGHTS_MIN,
                                nights_max=config.NIGHTS_MAX,
                                pax=config.PAX,
                            )
                            logger.info("  -> %d offre(s)", len(offers))
                            all_offers.extend(offers)
                        except Exception:
                            logger.exception(
                                "Échec de recherche pour %s / %s / %s (on continue)",
                                provider_name,
                                destination.code,
                                departure_date,
                            )
                        provider.polite_delay()

                context.close()
        finally:
            browser.close()

    return all_offers
