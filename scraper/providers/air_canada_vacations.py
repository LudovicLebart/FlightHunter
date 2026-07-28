from providers.generic import GenericPackageProvider, Selectors

# Sélecteurs candidats — À VÉRIFIER contre le site réel (voir README.md).
SELECTORS = Selectors(
    origin_input=[
        "input[name='origin']",
        "input[id*='origin' i]",
        "[data-testid='origin-input']",
    ],
    destination_input=[
        "input[name='destination']",
        "input[id*='destination' i]",
        "[data-testid='destination-input']",
    ],
    departure_date=[
        "input[name='departureDate']",
        "input[id*='depart' i]",
        "[data-testid='departure-date']",
    ],
    return_date=[
        "input[name='returnDate']",
        "input[id*='return' i]",
        "[data-testid='return-date']",
    ],
    nights_min=["input[name='nightsMin']", "[data-testid='nights-min']"],
    nights_max=["input[name='nightsMax']", "[data-testid='nights-max']"],
    pax_input=["input[name='adults']", "[data-testid='pax-input']"],
    search_button=[
        "button[type='submit']",
        "[data-testid='search-button']",
        "button:has-text('Rechercher')",
        "button:has-text('Search')",
    ],
    result_card=[
        "[data-testid='result-card']",
        ".package-card",
        ".vacation-package-card",
        "li.result-item",
    ],
    hotel_name=["[data-testid='hotel-name']", ".hotel-name", "h3"],
    price=["[data-testid='price']", ".price-total", ".price"],
    board_type=["[data-testid='board-type']", ".board-type", ".meal-plan"],
    nights=["[data-testid='nights']", ".nights", ".duration"],
)


class AirCanadaVacationsProvider(GenericPackageProvider):
    """Vacances Air Canada (vacances.aircanada.com) — forfaits tout compris."""

    name = "air_canada_vacations"
    base_url = "https://www.vacances.aircanada.com/fr-ca/"
    selectors = SELECTORS
