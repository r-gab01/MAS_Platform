# Logica per l'upload e l'indicizzazione dei file
import uuid

from sqlalchemy.orm import Session
from app.shared.schemas.kb_schemas import KnowledgeBaseCreate
from app.shared.persistence.models import KnowledgeBaseModel
from app.shared.persistence import kb_db
from app.shared.storage import storage_provider

def create_local_kb(db: Session, kb_data: KnowledgeBaseCreate) -> KnowledgeBaseModel:
    """
    Logica di business per gestire la creazione di un kb in locale (ossia con memorizzazione file in locale)
    """

    # 1. Controllo nome kb univoco
    if kb_db.get_kb_by_name(db, kb_data.name):
        raise ValueError(f"Un agente con nome {kb_data.name} esiste già")

    db_kb = kb_db.create_kb(db, kb_data)
    if not db_kb:
        raise ValueError(f"Errore durante la creazione della Knowledge Base")

    # Creo KB in locale
    storage_provider.create_kb_folder(db_kb.id)

    return db_kb


def get_all_kbs(db: Session)-> list[KnowledgeBaseModel]:
    """
    Logica di business per ottenere tutte le kb dal database
    """
    return kb_db.get_all_kbs(db)


def get_kb_by_id(db: Session, kb_id: uuid.UUID ) -> KnowledgeBaseModel:
    db_kb = kb_db.get_kb_by_id(db, kb_id)
    if not db_kb:
        raise ValueError(f"La Knowledge Base con id='{kb_id}' non trovata")
    return db_kb


def update_kb(db: Session, kb_id: uuid.UUID, kb_data: KnowledgeBaseCreate) -> KnowledgeBaseModel:
    """
    Logica di business per consentire la modifica della kb specificata
    """

    # Controllo id esistente
    db_kb = kb_db.get_kb_by_id(db, kb_id)
    if not db_kb:
        raise ValueError(f"La Knowledge Base con id='{kb_id}' non trovata")

    # Verifico che il nome non sia già usato da un' altra kb
    if kb_data.name != db_kb.name:
        existing_kb = kb_db.get_other_kb_with_name(db, name=kb_data.name, kb_id=kb_id)
        if existing_kb:
            raise ValueError(f"Una KnowledgeBase con nome '{kb_data.name}' esiste già")

    # Aggiorno KB
    print(f"Servizio: Agiorno la KB con id='{kb_id}'...")
    return kb_db.update_kb(db=db, kb_old_model=db_kb, kb_data=kb_data, kb_id=kb_id)


def delete_kb(db:Session, kb_id: uuid.UUID):
    """
    Logica di business per eliminare kb specificata
    """

    db_kb = kb_db.get_kb_by_id(db, kb_id)
    if not db_kb:
        raise ValueError(f"La Knowledge Base con id='{kb_id}' non trovata")
    kb_db.delete_kb(db, db_kb)
    storage_provider.delete_kb_folder(db_kb.id)