import os

from langchain_postgres import PGVector
from langchain_core.documents import Document
from typing import List

from app.shared.factories import EmbeddingFactory

# Nome della tabella dove LangChain salverà i vettori
VECTOR_TABLE_NAME = "pg_embeddings"
COLLECTION_TABLE_NAME = "pg_collections"


def get_connection_string():
    # Usa il driver psycopg (v3) che è quello supportato da langchain-postgres
    # Assicurati che DATABASE_URL inizi con "postgresql+psycopg://"
    url = os.getenv("DATABASE_URL")
    if "postgresql://" in url and "psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://")
    return url


def get_vector_store(kb_id: str):
    """
    Restituisce un'istanza di PGVector configurata.

    NOTA: Usiamo 'kb_id' come nome della 'collection'. 
    In questo modo, ogni Knowledge Base è isolata logicamente nel DB.
    """
    connection_string = get_connection_string()

    # 1. Ottieni il modello di embedding (es. OpenAI, Titan)
    # Potresti volerlo configurabile per KB, per ora usiamo default
    embeddings = EmbeddingFactory.get_embedding_model(provider="huggingface")

    # 2. Inizializza lo store
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=str(kb_id),     # isoliamo le collections tramite id delle nostre kb
        connection=connection_string,
        use_jsonb=True,
    )
    return vector_store


def add_documents_to_vector_store(kb_id: str, documents: List[Document]):
    """Salva i documenti (chunks) nel DB vettoriale."""
    vector_store = get_vector_store(kb_id)  # fornendo kb_id abbiamo un vector store che punta alla collezione (KnowledgeBase) desiderata
    vector_store.add_documents(documents)


def delete_collection(kb_id: str):
    """Elimina una specifica collezione (una nostra KB)."""
    vector_store = get_vector_store(kb_id)
    vector_store.delete_collection()

def delete_documents_from_collection(kb_id: str, filename: str):
    """Rimuove i vettori associati a un documento dalla collezione"""
    vector_store = get_vector_store(kb_id)

    filter_query={
        "filename": filename
    }
    try:
        vector_store.delete(filter=filter_query)
    except Exception as e:
        print(f"❌ Errore durante l'eliminazione del documento {filename}: {e}")