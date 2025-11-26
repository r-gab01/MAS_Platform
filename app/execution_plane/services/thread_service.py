import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.shared.persistence.models import ChatThreadModel
from app.shared.schemas.thread_schemas import ChatThreadCreate
from app.shared.persistence import thread_db


def create_update_thread(db: Session, thread_data: ChatThreadCreate) -> Optional[ChatThreadModel]:
    """
        Logica di business per creare un thread chat solo se non eisiste già
        ritorna una tupla: (chat, boolean con True se ha creato la chat)
    """
    # tid_uuid = uuid.UUID(str(thread_data.thread_id)) TODO: usare
    exists = thread_db.get_thread(db=db, thread_id=thread_data.thread_id)    #TODO: tid_uuid
    if not exists:
        new_thread = thread_db.create_thread(db=db, thread_data=thread_data)
        return new_thread
    else:
        exists = thread_db.update_thread(db=db, thread_id=thread_data.thread_id, old_thread=exists)
        return exists


def get_thread(db: Session, thread_id: str) -> Optional[ChatThreadModel]:
    """
    Logica di business per ottenere i dati di un thread
    """
    thread = thread_db.get_thread(db=db, thread_id=thread_id)
    if thread is None:
        raise ValueError(f"Thread con id='{thread_id}' non trovato")
    return thread

def get_threads_list(db: Session) -> list[ChatThreadModel]:
    """
    Logica di business per ottenere la lista di tutte le chat
    """
    threads = thread_db.get_all_threads(db=db)
    return threads


def delete_thread(db: Session, thread_id: str):
    """
    Logica di business per eliminare una chat
    """
    db_thread = thread_db.get_thread(db=db, thread_id=thread_id)
    if db_thread is None:
        raise ValueError(f"Thread con id='{thread_id}' non trovato")
    thread_db.delete_thread(db=db, db_thread=db_thread)
    return None