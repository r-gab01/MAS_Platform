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