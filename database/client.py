# pyrefly: ignore [missing-import]
from astrapy import DataAPIClient
from astrapy.info import CollectionDefinition, CollectionVectorOptions
from astrapy.constants import VectorMetric
from config import ASTRA_DB_API_ENDPOINT, ASTRA_DB_APPLICATION_TOKEN

_client = DataAPIClient()
_db = _client.get_database(
    api_endpoint=ASTRA_DB_API_ENDPOINT,
    token=ASTRA_DB_APPLICATION_TOKEN,
)

def get_collection(name: str):
    """Verilen isimde AstraDB koleksiyonu döndürür."""
    return _db.get_collection(name)

def ensure_collection(name: str, dimension: int = None) -> None:
    """Koleksiyon yoksa oluşturur, varsa dokunmaz.
    dimension verilirse vektör koleksiyonu (cosine metric) oluşturur.
    """
    try:
        if dimension:
            definition = CollectionDefinition(
                vector=CollectionVectorOptions(dimension=dimension, metric=VectorMetric.COSINE)
            )
            _db.create_collection(name, definition=definition)
        else:
            _db.create_collection(name)
    except Exception:
        pass  # Koleksiyon zaten var
