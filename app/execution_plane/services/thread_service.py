import json
from typing import Optional
from app.shared.persistence.models import ChatThreadModel
import uuid
import re

import asyncio
from typing import AsyncGenerator
from sqlalchemy.orm import Session
from fastapi import HTTPException

# I tuoi import
from app.shared.factories.checkpointer_factory import CheckpointFactory
from app.shared.persistence import team_db, thread_db, message_db
from app.shared.persistence.models.message_model import MessageType
from app.shared.schemas.thread_schemas import ChatThreadCreate

from app.execution_plane.runtime.graph_factory import build_team_graph


def clean_langchain_id(dirty_id: str) -> uuid.UUID:
    """Helper per pulire ID sporchi di LangChain"""
    if not dirty_id: return uuid.uuid4()
    match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', str(dirty_id))
    return uuid.UUID(match.group(0)) if match else uuid.uuid4()



class ThreadService:

    @staticmethod
    async def prepare_chat(db: Session, team_id: int, thread_id: str, message: str):
        """wrapper asincrono per la preparazione della chat. Se la preparazione chat fallisce possiamo bloccare tutto."""
        await asyncio.to_thread(
            ThreadService._prepare_conversation_sync,
            db, team_id, thread_id, message
        )


    @staticmethod
    def _prepare_conversation_sync(db: Session, team_id: int, thread_id: str, message: str):
        """Verifica team, crea thread e salva messaggio utente."""
        # 1. Check Team
        db_team = team_db.get_team_by_id(db=db, team_id=team_id)
        if not db_team:
            raise HTTPException(status_code=404, detail=f"Team con id='{team_id}' non trovato.")

        # 2. Upsert Thread
        db_thread = thread_db.get_thread(db=db, thread_id=thread_id)
        if not db_thread:
            thread_db.create_thread(
                db=db,
                thread_data=ChatThreadCreate(thread_id=thread_id, title=f"Chat {thread_id[:8]}")
            )
        else:
            thread_db.update_thread(db=db, old_thread=db_thread)

        # 3. Save User Message
        message_db.add_message(
            db=db,
            thread_id=thread_id,
            content=message,
            msg_type=MessageType.HUMAN
        )


    @staticmethod
    async def run_chat_stream(
            db: Session,
            team_id: int,
            thread_id: str,
            user_message: str
    ) -> AsyncGenerator[str, None]:
        """
        Orchestra l'intero flusso di chat:
        1. Setup DB (Sync -> ThreadPool: thread separato per non bloccare FastApi)
        2. Esecuzione Grafo (Async)
        3. Salvataggio Risposta (Sync -> ThreadPool)
        """

        # --- FASE 2: ESECUZIONE GRAFO (ASYNC) ---
        async with CheckpointFactory.get_checkpointer() as checkpointer:

            # Costruzione grafo
            try:
                graph = await asyncio.to_thread(build_team_graph, db, team_id, checkpointer)
            except Exception as e:
                yield f"data: Error: {str(e)}\n\n"
                return


            config = {"configurable": {"thread_id": thread_id}}
            inputs = {"messages": [("user", user_message)]}


            # STREAM
            print(f"--- START STREAM Thread {thread_id} ---")

            final_message_to_save = None # Variabile "buffer" per ricordare l'ultimo messaggio AI valido visto

            try:
                # tramite astream generiamo flusso di eventi per ogni modifica nello stato del Grafo (fra cui la risposta man mano prodotta dall'agente)
                async for event in graph.astream(inputs, config=config, stream_mode="values"):
                    if "messages" in event:
                        last_msg = event["messages"][-1]    # Ultimo messaggio contiene il nuovo contenuto generato nel nodo

                        # Prepariamo un payload strutturato
                        payload = {
                            "type": last_msg.type,
                            "content": last_msg.content,
                        }
                        if last_msg.type == "ai":
                            final_message_to_save = last_msg

                        # Se è un messaggio AI, includiamo eventuali chiamate ai tool
                        if last_msg.type == "ai" and last_msg.tool_calls:
                            payload["tool_calls"] = last_msg.tool_calls

                        # Se è un messaggio Tool, includiamo il nome del tool che ha risposto
                        if last_msg.type == "tool":
                            payload["name"] = last_msg.name
                            payload["tool_call_id"] = last_msg.tool_call_id

                        # Invio via SSE (serializzato in JSON)
                        # Sostituiamo i newline per non rompere il protocollo SSE
                        json_data = json.dumps(payload)
                        yield f"data: {json_data}\n\n"       # formato Server-Sent Events (SSE)

            except Exception as e:
                print(f" Errore durante streaming: {e}")
                yield f"data: Error: {str(e)}\n\n"

            # --- FASE 3: SALVATAGGIO FINALE (SYNC OFF-LOAD) ---
            if final_message_to_save:
                await asyncio.to_thread(
                    ThreadService._save_ai_message_sync,
                    db, thread_id, final_message_to_save
                )



    @staticmethod
    def _save_ai_message_sync(db: Session, thread_id: str, ai_msg):
        """Salva il messaggio finale dell'AI."""
        content = ai_msg.content
        if isinstance(content, list):
            content = "".join(str(item) for item in content)

        # Qui potresti avere la tua logica di clean_id
        lang_id = getattr(ai_msg, 'id', None)
        clean_id = clean_langchain_id(lang_id)

        message_db.add_message(
            db=db,
            id=clean_id,
            thread_id=thread_id,
            content=str(content),
            msg_type=MessageType.AI,
        )

    @staticmethod
    def get_thread(db: Session, thread_id: str) -> Optional[ChatThreadModel]:
        """
        Logica di business per ottenere i dati di un thread
        """
        thread = thread_db.get_thread(db=db, thread_id=thread_id)
        if thread is None:
            raise ValueError(f"Thread con id='{thread_id}' non trovato")
        return thread


    @staticmethod
    def get_threads_list(db: Session) -> list[ChatThreadModel]:
        """
        Logica di business per ottenere la lista di tutte le chat
        """
        threads = thread_db.get_all_threads(db=db)
        return threads


    @staticmethod
    def delete_thread(db: Session, thread_id: str):
        """
        Logica di business per eliminare una chat
        """
        db_thread = thread_db.get_thread(db=db, thread_id=thread_id)
        if db_thread is None:
            raise ValueError(f"Thread con id='{thread_id}' non trovato")
        thread_db.delete_thread(db=db, db_thread=db_thread)
        return None