from sqlalchemy import String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from ..db_client import Base


class ChatThreadModel(Base):
    __tablename__ = "chat_threads"

    # Usiamo una stringa (UUID) come ID perché LangGraph usa stringhe per i thread_id
    thread_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String, nullable=True)  # Es. "Analisi Ebook Palermo"
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # In futuro qui aggiungerai user_id per il multi-tenant
    # user_id: Mapped[int] = mapped_column(Integer, index=True)