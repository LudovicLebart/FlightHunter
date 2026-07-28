from __future__ import annotations

import csv
import json
import logging

import config
from models import Offer

logger = logging.getLogger("scraper.aggregate")


def sort_and_filter(offers: list[Offer], max_price: float | None = None) -> list[Offer]:
    max_price = config.BUDGET_MAX_CAD if max_price is None else max_price
    filtered = [o for o in offers if o.price_total_cad <= max_price]
    filtered.sort(key=lambda o: o.price_total_cad)
    logger.info(
        "%d offre(s) au total, %d sous le budget de %s $ CAD",
        len(offers),
        len(filtered),
        max_price,
    )
    return filtered


def export_csv(offers: list[Offer], path: str) -> None:
    fieldnames = [
        "provider",
        "destination_code",
        "destination_name",
        "sargassum_risk",
        "departure_date",
        "return_date",
        "nights",
        "price_total_cad",
        "price_per_person",
        "hotel_name",
        "board_type",
        "url",
        "scraped_at",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for offer in offers:
            writer.writerow(offer.to_dict())


def export_json(offers: list[Offer], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([o.to_dict() for o in offers], f, ensure_ascii=False, indent=2)


def print_top(offers: list[Offer], n: int = 10) -> None:
    if not offers:
        print("Aucune offre trouvée sous le budget.")
        return

    print(f"\nTop {min(n, len(offers))} offres (triées par prix total) :\n")
    for i, o in enumerate(offers[:n], start=1):
        risk_flag = " ⚠️ sargasses (risque modéré)" if o.sargassum_risk == "moderate" else ""
        print(
            f"{i:2d}. {o.price_total_cad:>7.0f} $ CAD "
            f"({o.price_per_person:.0f} $/pers.) — {o.hotel_name} "
            f"({o.destination_name}){risk_flag}\n"
            f"    {o.provider} | départ {o.departure_date} | {o.nights} nuits | {o.url}"
        )
