import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.shared.persistence.db_client import get_db
from app.control_plane.services import kb_service
from app.shared.schemas.kb_schemas import KnowledgeBaseRead, KnowledgeBaseCreate

router = APIRouter(
    prefix="/api/v1/kb",
    tags=["KnowledgeBases"],
)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=KnowledgeBaseRead)
def create_knowledge_base(
        kb_data: KnowledgeBaseCreate,
        db: Session = Depends(get_db)
):
    """
    Crea una nuova knowledge base nel sistema
    """
    try:
        created_kb = kb_service.create_local_kb(db, kb_data)
        return created_kb
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[KnowledgeBaseRead])
def read_kb(db: Session = Depends(get_db)):
    """
    Restituisce la lista di Knowledge Bases nel sistema
    """
    try:
        return kb_service.get_all_kbs(db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{kb_id}", response_model=list[KnowledgeBaseRead])
def read_kb(
        kb_id: uuid.UUID,
        db: Session = Depends(get_db),

):
    """
    Restituisce la lista di Knowledge Bases nel sistema
    """
    try:
        return kb_service.get_kb_by_id(db, kb_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))