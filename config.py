import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Amadeus API Keys ---
AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")

# --- Firebase Configuration ---
# Path to your Firebase service account key
FIREBASE_KEY_PATH = os.path.join(os.path.dirname(__file__), "backend", "config", "serviceAccountKey.json")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

# --- Application Settings ---
APP_ID_TARGET = os.getenv("APP_ID_TARGET", "FlightHunter_App")
USER_ID_TARGET = os.getenv("USER_ID_TARGET", "DefaultUser")
