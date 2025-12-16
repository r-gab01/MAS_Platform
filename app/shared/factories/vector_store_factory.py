import os
from sqlalchemy import create_engine, Engine
from langchain_postgres import PGVector
from app.shared.factories.embedding_factory import EmbeddingFactory


class VectorStoreFactory:
    """
    Factory Singleton per la gestione efficiente delle connessioni PGVector.
    Gestisce un unico SQLAlchemy Engine condiviso per evitare connection leaks.
    """

    # Variabile di classe per mantenere l'istanza unica dell'Engine (Singleton)
    _engine: Engine = None

    @staticmethod
    def _get_connection_string() -> str:
        """Normalizza la stringa di connessione per il driver psycopg (v3)."""
        url = os.getenv("DATABASE_URL", "")
        if not url:
            raise ValueError("DATABASE_URL environment variable is not set.")

        # langchain-postgres richiede il driver psycopg 3
#        if "postgresql://" in url and "psycopg" not in url:
#            return url.replace("postgresql://", "postgresql+psycopg://")
        return url

    @classmethod
    def get_engine(cls) -> Engine:
        """
        Ritorna l'Engine condiviso.
        Se non esiste ancora, lo crea (Lazy Initialization).
        """
        if cls._engine is None:
            print("🔌 VectorStoreFactory: Inizializzazione Database Engine Pool...")
            cls._engine = create_engine(
                cls._get_connection_string(),
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_pre_ping=True,
            )
        return cls._engine


    @classmethod
    def get_vector_store(cls, kb_id: str) -> PGVector:
        """
        Restituisce un'istanza di PGVector configurata per una specifica KB.

        :param kb_id: L'ID della Knowledge Base (usato come nome della collection)
        :return: Istanza pronta all'uso di PGVector
        """
        # 1. Otteniamo l'Engine condiviso (non ne creo uno nuovo!)
        engine = cls.get_engine()

        # 2. Otteniamo il modello di embedding
        embeddings = EmbeddingFactory.get_embedding_model(provider="huggingface")

        # 3. Restituiamo l'oggetto PGVector collegato al pool esistente
        return PGVector(
            connection=engine,  # Passiamo l'engine, NON la stringa
            embeddings=embeddings,
            collection_name=str(kb_id),
            use_jsonb=True,
        )


    @classmethod
    def dispose(cls):
        """
        Chiude tutte le connessioni del pool.
        Utile per il Graceful Shutdown dell'applicazione.
        """
        if cls._engine:
            print("🔌 VectorStoreFactory: Chiusura Database Engine...")
            cls._engine.dispose()
            cls._engine = None