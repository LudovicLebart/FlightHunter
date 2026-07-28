"""Point d'entrée CLI du scraper brute force tout-inclus.

Voir README.md pour le contexte, la portée et les limites connues.
"""
from __future__ import annotations

import argparse
import datetime
import logging
import os

import config
from aggregate import export_csv, export_json, print_top, sort_and_filter
from brute_force import run_brute_force


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recherche brute force de forfaits tout-inclus")
    parser.add_argument(
        "--provider",
        action="append",
        dest="providers",
        choices=list(config.ENABLED_PROVIDERS),
        help="Limiter à un provider (répétable). Par défaut: tous les providers activés.",
    )
    parser.add_argument(
        "--max-price",
        type=float,
        default=None,
        help=f"Budget max en CAD (défaut: {config.BUDGET_MAX_CAD})",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Logs verbeux + dumps HTML/capture en cas d'erreur (navigateur toujours headless)",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Navigateur visible (nécessite un serveur d'affichage — ne fonctionne PAS dans un "
        "conteneur/Codespace sans xvfb)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    offers = run_brute_force(provider_names=args.providers, debug=args.debug, headed=args.headed)
    filtered = sort_and_filter(offers, max_price=args.max_price)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(config.OUTPUT_DIR, f"offers_{ts}.csv")
    json_path = os.path.join(config.OUTPUT_DIR, f"offers_{ts}.json")
    export_csv(filtered, csv_path)
    export_json(filtered, json_path)

    print_top(filtered, n=10)
    print(f"\nRésultats complets : {csv_path} / {json_path}")


if __name__ == "__main__":
    main()
