# Cuore della tua persistenza. Configura la connessione al database PostgreSQL (es. tramite SQLAlchemy) e
# gestisce l'engine e le sessioni che tutti gli altri file useranno.

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# Carica l'URL del tuo DB PostgreSQL (con pgvector) dal file .env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL non è impostato nel file .env")

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10
)

# Factory per creare nuove sessioni di DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class per tutti i nostri modelli SQLAlchemy
# erediteremo da questa per specificare le colonne e i tipi di dati delle tabelle
class Base(DeclarativeBase):
    pass

# Funzione per creare tabelle (da chiamare all'avvio dell'app)
def create_db_and_tables():
    Base.metadata.create_all(bind=engine)

# Dependency di FastAPI: fornisce una sessione DB a ogni richiesta API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()