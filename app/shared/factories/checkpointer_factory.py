# Usiamo PostgreSQL per la memoria (checkpointing). Il checkpointing permette di
# avere persistenza dei dati e riprendere conversazioni interrotte.
# Tramite questa factory abbiamo un gestore centralizzato per il pool di connessioni.
# Il pool permette di non aprire una nuova connessione al DB ad ogni messaggio.

import os
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


class CheckpointFactory:
    """
    Singleton Factory per gestire il pool di connessioni e il checkpointer di LangGraph.
    """
    _pool: AsyncConnectionPool = None   # Variabile per gestire il Singleton: mantiene il pool di connessioni attivo

    @staticmethod   # Metodo statico perchè non ha bisogno dell'istanza e delle variabili della classe, recupera solo le credenziali del db
    def _get_database_url():
        url = os.getenv("POSTGRES_URI")
        if not url:
            raise ValueError("POSTGRES_URI non impostato")
        return url

    @classmethod    # metodo di classe: riceve la classe stessa (cls) per gestire le sue variabili e far funzionare il Singleton
    async def initialize(cls):
        """Inizializza il pool globale. Da chiamare allo startup dell'app."""
        if cls._pool is None:
            print("🔌 CheckpointFactory: Apertura Connection Pool...")

            # 1. Creazione Pool (closed)
            cls._pool = AsyncConnectionPool(
                conninfo=cls._get_database_url(),
                max_size=20,
                open=False,
                kwargs={"autocommit": True}
            )

            # 2. Apertura asincrona esplicita
            await cls._pool.open()
            await cls._pool.wait()
            print("✅ CheckpointFactory: Pool Aperto e pronto.")

    @classmethod
    async def close(cls):
        """Chiude il pool. Da chiamare allo shutdown dell'app."""
        if cls._pool:
            print("🔌 CheckpointFactory: Chiusura Pool...")
            await cls._pool.close()
            cls._pool = None

    @classmethod
    @asynccontextmanager
    async def get_checkpointer(cls):
        """
        Context manager che restituisce un AsyncPostgresSaver usando il pool condiviso.
        """
        if cls._pool is None:
            # Auto-inizializzazione lazy (opzionale, ma utile per sicurezza)
            await cls.initialize()

        # Istanzia il saver con il pool esistente (in cls._pool abbiamo un oggetto pool già istanziato: Magia del Singleton)
        checkpointer = AsyncPostgresSaver(cls._pool)

        # Assicura che le tabelle esistano (idempotente)
        await checkpointer.setup()

        try:
            yield checkpointer
        finally:
            # Qui non chiudiamo il pool! Il pool vive finché vive l'app.
            pass

'''
def get_database_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL non impostato")
    return url


async def init_checkpointer_pool():
    """Inizializza il pool globale. Da chiamare allo startup."""
    global _CHECKPOINT_POOL
    if _CHECKPOINT_POOL is None:
        print("🔌 Apertura Connection Pool per Checkpointer...")

        # 1. Creiamo l'oggetto MA gli diciamo di NON aprirsi subito (open=False)
        _CHECKPOINT_POOL = AsyncConnectionPool(
            conninfo=get_database_url(),
            max_size=20,
            open=False,  # <--- QUESTA È LA CHIAVE PER RIMUOVERE IL WARNING
            kwargs = {"autocommit": True}
        )

        # 2. Apriamo il pool esplicitamente in modo asincrono
        await _CHECKPOINT_POOL.open()

        # 3. Opzionale: aspettiamo che sia pronto
        await _CHECKPOINT_POOL.wait()
        print("✅ Connection Pool Aperto.")


async def close_checkpointer_pool():
    """Chiude il pool. Da chiamare allo shutdown."""
    global _CHECKPOINT_POOL
    if _CHECKPOINT_POOL:
        print("🔌 Chiusura Connection Pool Checkpointer...")
        await _CHECKPOINT_POOL.close()
        _CHECKPOINT_POOL = None


@asynccontextmanager
async def get_checkpointer():
    """
    Context manager che restituisce un'istanza di AsyncPostgresSaver pronta all'uso.
    Usa il pool globale.
    """
    global _CHECKPOINT_POOL
    if _CHECKPOINT_POOL is None:
        await init_checkpointer_pool()

    # Crea il saver usando il pool esistente
    checkpointer = AsyncPostgresSaver(_CHECKPOINT_POOL)

    # IMPORTANTE: Assicura che le tabelle di sistema di LangGraph esistano
    # (checkpoints, checkpoint_blobs, etc.)
    await checkpointer.setup()

    yield checkpointer
'''