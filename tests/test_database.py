from astrapy import DataAPIClient
from config import ASTRA_DB_API_ENDPOINT, ASTRA_DB_APPLICATION_TOKEN

# Initialize the client
client = DataAPIClient()
db = client.get_database(
  api_endpoint=ASTRA_DB_API_ENDPOINT,
  token=ASTRA_DB_APPLICATION_TOKEN,
)

print(f"Connected to Astra DB: {db.list_collection_names()}")
