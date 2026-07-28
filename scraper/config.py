"""Paramètres de la recherche brute force tout-inclus.

Module indépendant du backend officiel (voir README.md du dossier scraper/).
Modifie librement les valeurs ci-dessous plutôt que de les hardcoder ailleurs.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field


# --- Recherche ---------------------------------------------------------

ORIGIN = "YUL"  # Montréal-Trudeau

# Fenêtre de départ : plage de dates fixe (bornes incluses).
DEPARTURE_START = datetime.date(2026, 8, 2)
DEPARTURE_END = datetime.date(2026, 8, 9)

def departure_dates() -> list[datetime.date]:
    n_days = (DEPARTURE_END - DEPARTURE_START).days
    return [DEPARTURE_START + datetime.timedelta(days=d) for d in range(0, n_days + 1)]


NIGHTS_MIN = 9
NIGHTS_MAX = 15

PAX = 2  # nombre de passagers — ajuste si besoin, non précisé par l'utilisateur
BUDGET_MAX_CAD = 12_000  # budget total pour le voyage (tous passagers confondus)

BOARD_TYPE = "all_inclusive"

# --- Voyagistes ----------------------------------------------------------

# Providers activés par défaut. Sunwing et WestJet Vacances sont exclus
# volontairement (préavis de grève sur des vacances déjà payées par
# l'utilisateur — cf. contexte de la demande).
ENABLED_PROVIDERS = ["transat", "air_canada_vacations"]
EXCLUDED_PROVIDERS = ["sunwing", "westjet"]


# --- Destinations & risque de sargasses -----------------------------------
# Le risque de sargasses est saisonnier et varie semaine par semaine / plage
# par plage. Ces tags sont des généralités (juillet-octobre = haute saison
# de sargasses côté Caraïbes/Atlantique) et NE remplacent PAS une vérification
# des bulletins récents avant de réserver. Ce script n'a pas accès à des
# données de sargasses en temps réel.

@dataclass(frozen=True)
class Destination:
    code: str
    name: str
    country: str
    sargassum_risk: str  # "low" | "moderate" | "high"


DESTINATIONS: list[Destination] = [
    # Cuba — côté nord/ouest des Caraïbes, historiquement peu touché.
    Destination("VRA", "Varadero", "Cuba", "low"),
    Destination("CCC", "Cayo Coco", "Cuba", "low"),
    Destination("SNU", "Cayo Santa Maria", "Cuba", "low"),
    # Mexique — côte Pacifique, hors zone d'échouage des sargasses.
    Destination("PVR", "Puerto Vallarta", "Mexique", "low"),
    Destination("SJD", "Los Cabos", "Mexique", "low"),
    Destination("HUX", "Huatulco", "Mexique", "low"),
    # Jamaïque — variable selon la côte, à vérifier avant réservation.
    Destination("MBJ", "Montego Bay", "Jamaïque", "moderate"),
    # République dominicaine — côte nord généralement moins touchée que Punta Cana.
    Destination("POP", "Puerto Plata", "République dominicaine", "moderate"),
    # Exclues par défaut (risque élevé de sargasses juillet-octobre) :
    # Destination("CUN", "Cancún / Riviera Maya", "Mexique", "high"),
    # Destination("PUJ", "Punta Cana", "République dominicaine", "high"),
]

# Inclure ou non les destinations à risque "modéré" (celles à risque "high"
# restent toujours exclues, conformément à la demande "sans sargasses").
INCLUDE_MODERATE_SARGASSUM_RISK = True


def active_destinations() -> list[Destination]:
    allowed = {"low"} | ({"moderate"} if INCLUDE_MODERATE_SARGASSUM_RISK else set())
    return [d for d in DESTINATIONS if d.sargassum_risk in allowed]


# --- Scraping / politesse -------------------------------------------------

REQUEST_DELAY_SECONDS = (3, 7)  # délai aléatoire min/max entre deux requêtes
PAGE_TIMEOUT_MS = 30_000
NAV_RETRIES = 2

OUTPUT_DIR = "output"
DEBUG_DIR = "output/debug"
