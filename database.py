from astrapy import DataAPIClient
from config import ASTRA_DB_API_ENDPOINT, ASTRA_DB_APPLICATION_TOKEN

def get_db():
    """Initializes and returns the AstraDB database instance."""
    if not ASTRA_DB_API_ENDPOINT or not ASTRA_DB_APPLICATION_TOKEN:
        print("Warning: AstraDB credentials are missing from .env")
        return None

    client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
    db = client.get_database_by_api_endpoint(ASTRA_DB_API_ENDPOINT)
    return db

if __name__ == "__main__":
    db = get_db()
    if db:
        print("Successfully connected to AstraDB.")
