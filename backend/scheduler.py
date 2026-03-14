import schedule
import time
import logging

class TaskScheduler:
    """Manages scheduled tasks for the FlightHunter bot."""

    def __init__(self, api_client):
        self.logger = logging.getLogger(__name__)
        self.api_client = api_client
        self.logger.info("Task scheduler initialized.")

    def schedule_flight_search(self, origin, destination, departure_date, return_date=None, adults=1, interval_minutes=60):
        """Schedules a recurring flight search."""
        self.logger.info(f"Scheduling flight search for {origin}-{destination} every {interval_minutes} minutes.")
        
        # Define the job function
        def job():
            self.logger.info(f"Running scheduled flight search for {origin}-{destination}...")
            flights = self.api_client.search_flights(origin, destination, departure_date, return_date, adults)
            # TODO: Process the flight results (e.g., save to database, send notifications)
            self.logger.info(f"Found {len(flights)} flights.")

        # Schedule the job
        schedule.every(interval_minutes).minutes.do(job)

    def run_pending(self):
        """Runs all pending scheduled tasks."""
        schedule.run_pending()
