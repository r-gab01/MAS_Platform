from typing import Optional

from sqlalchemy.orm import Session

from app.shared.persistence.models import ChatThreadModel
from app.shared.schemas.thread_schemas import ChatThreadCreate
from app.shared.persistence import thread_db


def create_thread_if_not_exists(db: Session, thread_data: ChatThreadCreate) -> Optional[ChatThreadModel]:
    """
        Logica di business per creare un thread chat solo se non eisiste già
    """
    exists = thread_db.get_thread(db=db, thread_id=thread_data.thread_id)
    if not exists:
        new_thread = thread_db.create_thread(db=db, thread_data=thread_data)
        return new_thread
    return exists

def get_chats_list(db: Session) -> list[ChatThreadModel]:
    """
    Logica di business per ottenere la lista di tutte le chat
    """
    threads = thread_db.get_all_threads(db=db)
    return threads


def delete_agent(db: Session, thread_id: str):
    """
    Logica di business per eliminare una chat
    """
    db_thread = thread_db.get_thread(db=db, thread_id=thread_id)
    if db_thread is None:
        raise ValueError(f"Thread con id='{thread_id}' non trovato")
    thread_db.delete_thread(db=db, db_thread=db_thread)
    return None