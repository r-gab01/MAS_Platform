from datetime import datetime, timezone
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.shared.persistence.models import KnowledgeBaseModel
from app.shared.schemas.kb_schemas import KnowledgeBaseCreate


def create_kb(db: Session, kb_schema: KnowledgeBaseCreate) -> KnowledgeBaseModel:
    """
    Salva una nuova kb nel DB.
    """

    db_kb = KnowledgeBaseModel(**kb_schema.model_dump())

    db.add(db_kb)
    db.commit()
    db.refresh(db_kb)

    return db_kb


def filter_kbs(db: Session, kb_ids: list) -> list:
    """
    Filtra la lista delle kb in ingresso restituendo la lista di quelle realmente esistenti nel db
    """
    return db.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.id.in_(kb_ids)).all()


def get_kb_by_name(db: Session, name: str) -> Optional[KnowledgeBaseModel]:
    """
    Query per ottenere (e verificare) esistenza della kb con nome specificato
    """
    return db.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.name == name).first()


def get_all_kbs(db: Session) -> list:
    """
    Restituisce la lista delle bd memorizzate nel db
    """
    return db.query(KnowledgeBaseModel).all()


def get_kb_by_id(db: Session, kb_id: uuid.UUID) -> Optional[KnowledgeBaseModel]:
    """
    Query per ottenere la kb con id specificato dal DB
    """
    return db.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.id == kb_id).first()


def get_other_kb_with_name(db:Session, name: str, kb_id: uuid.UUID) -> Optional[KnowledgeBaseModel]:
    """
    Query per verificare se esiste già nel db una KB col nome specificato
    """
    return db.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.name == name).first()


def update_kb(db: Session, kb_old_model: KnowledgeBaseModel, kb_data: KnowledgeBaseCreate, kb_id: uuid.UUID) -> KnowledgeBaseModel:
    """
    Funzione che aggiorna una KB nel DB.
    """
    for key, value in kb_data.model_dump(exclude_unset=True).items():
        setattr(kb_old_model, key, value)

    kb_old_model.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(kb_old_model)
    return kb_old_model


def delete_kb(db: Session, kb_model: KnowledgeBaseModel):
    """
    Elimina una KB dal DB.
    """
    db.delete(kb_model)
    db.commit()