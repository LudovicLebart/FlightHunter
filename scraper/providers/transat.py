from providers.generic import GenericPackageProvider, Selectors

# Sélecteurs candidats — À VÉRIFIER contre le site réel (voir README.md).
# Chaque liste est essayée dans l'ordre par `Provider.first_matching`.
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
        "input[id*='departure' i]",
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
    ],
    result_card=[
        "[data-testid='result-card']",
        ".package-card",
        ".hotel-result-card",
        "li.result-item",
    ],
    hotel_name=["[data-testid='hotel-name']", ".hotel-name", "h3"],
    price=["[data-testid='price']", ".price-total", ".price"],
    board_type=["[data-testid='board-type']", ".board-type", ".meal-plan"],
    nights=["[data-testid='nights']", ".nights", ".duration"],
)


class TransatProvider(GenericPackageProvider):
    """Vacances Transat (vacances.transat.com) — forfaits tout compris."""

    name = "transat"
    # Domaine vérifié le 2026-07-28 (curl direct) : www.vacances.transat.com
    # n'existe pas (ERR_NAME_NOT_RESOLVED). Le vrai site est sous
    # www.transat.com, "widget-packageSearch" (AngularJS), protégé par
    # Incapsula. Sélecteurs internes toujours à vérifier — voir README.md.
    base_url = "https://www.transat.com/fr-CA/voyage-pas-cher/sud"
    selectors = SELECTORS
