import logging
from amadeus import Client, ResponseError
from config import AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET

class FlightApiClient:
    """Wrapper class for interacting with the Amadeus Flight Offers Search API."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            self.amadeus = Client(
                client_id=AMADEUS_CLIENT_ID,
                client_secret=AMADEUS_CLIENT_SECRET
            )
            self.logger.info("Successfully initialized Amadeus client.")
        except Exception as e:
            self.logger.error(f"Failed to initialize Amadeus client: {e}", exc_info=True)
            self.amadeus = None

    def search_flights(self, origin, destination, departure_date, return_date=None, adults=1):
        """Searches for flight offers."""
        if not self.amadeus:
            self.logger.error("Amadeus client is not initialized.")
            return []

        try:
            # Prepare API arguments
            args = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'departureDate': departure_date,
                'adults': adults
            }
            if return_date:
                args['returnDate'] = return_date

            response = self.amadeus.shopping.flight_offers_search.get(**args)
            return response.data
        except ResponseError as error:
            self.logger.error(f"Amadeus API Error: {error}", exc_info=True)
            return []
