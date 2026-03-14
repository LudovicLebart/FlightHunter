import logging
import firebase_admin
from firebase_admin import credentials, firestore, storage

class DatabaseService:
    """Handles Firebase database and storage services."""

    def __init__(self, key_path, storage_bucket):
        self.logger = logging.getLogger(__name__)
        self.db = None
        self.bucket = None
        self.offline_mode = False

        try:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred, {
                'storageBucket': storage_bucket
            })
            self.db = firestore.client()
            self.bucket = storage.bucket()
            self.logger.info("Successfully connected to Firebase.")
        except Exception as e:
            self.logger.error(f"Failed to initialize Firebase: {e}", exc_info=True)
            self.offline_mode = True
