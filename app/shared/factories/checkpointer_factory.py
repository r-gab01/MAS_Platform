# Usiamo PostgreSQL per la memoria (checkpointing). Il checkpointing permette di avere persistenza dei dati e riprendere conversazioni interrotte.
# Tramite questa factory abbiamo un gestore centralizzato per il pool di connessioni. Il pool permette di non aprire una nuova connessione al DB ad ogni messaggio.

import os
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# Variabile globale per mantenere il pool di connessioni attivo
_CHECKPOINT_POOL: AsyncConnectionPool = None


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