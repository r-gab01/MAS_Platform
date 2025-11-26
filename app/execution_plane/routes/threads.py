# API: /api/v1/chat/{team_id} (POST per avviare/continuare la chat)
import uuid
import re

from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.execution_plane.runtime.graph_factory import build_team_graph
from app.execution_plane.services import thread_service
from app.shared.persistence import team_db, message_db
from app.shared.persistence.db_client import get_db
from app.shared.factories.checkpointer_factory import get_checkpointer
from app.shared.persistence.models.message_model import MessageType
from app.shared.schemas.thread_schemas import ChatThreadCreate, ChatThreadRead

router = APIRouter(
    prefix="/api/v1/threads",
    tags=["Chat Execution"]
)

# Schema di input semplice mandato dal frontend per chattare
class ChatRequest(BaseModel):
    message: str = Field(..., description="Il messaggio dell'utente")
    team_id: int = Field(..., description="L'ID del team che deve rispondere")


def clean_langchain_id(dirty_id: str) -> uuid.UUID:
    """Helper per pulire ID sporchi di LangChain"""
    if not dirty_id: return uuid.uuid4()
    match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', str(dirty_id))
    return uuid.UUID(match.group(0)) if match else uuid.uuid4()



@router.post("/{thread_id}/chat")
async def chat_with_thread(
        thread_id: str,
        payload: ChatRequest,   # contenuto inviato di tipo ChatRequest
        db: Session = Depends(get_db)   # collegamento al db
):
    """
    ESEGUI CHAT (Streaming)
    Invia un messaggio a uno specifico thread e ottieni la risposta in streaming.
    Se il thread non esiste, viene creato.

    Flusso:
    L'utente clicca "Nuova Chat" sul Frontend.
    Il Frontend genera un UUID casuale in Javascript (es. 550e8400-e29b...).
    Il Frontend cambia subito l'URL del browser in /chat/550e8400....
    Quando l'utente scrive il primo messaggio, il Frontend chiama: POST /api/v1/threads/550e8400.../chat
    Il Backend (il tuo codice attuale) riceve l'ID, vede che non esiste nel database, lo crea al volo (create_thread_if_not_exists) e risponde.
    """
    # --- CONVERSIONE E VALIDAZIONE UUID: il frontend manda thread_id come str, dobbiamo convertirlo---
    '''
    try:
        thread_uuid = uuid.UUID(thread_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Thread ID non valido (deve essere un UUID)")
    '''

    try:
        # 1. Verifica team esistente
        db_team = team_db.get_team_by_id(db=db, team_id=payload.team_id)
        if db_team is None:
            raise HTTPException(status_code=404,
                                detail=f"Team con ID {payload.team_id} non trovato. Impossibile avviare la chat.")

        # 2. Creiamo la nuova chat (thread) nel db se non esiste
        thread_service.create_thread_if_not_exists(     # creo chat
            db=db,
            thread_data=ChatThreadCreate(
                thread_id=thread_id,
                title=f"Chat {str(thread_id)[:8]}"
            )
        )

        # 3. Salvataggio messaggio utente
        message_db.add_message(
            db=db,
            thread_id=thread_id,
            content=payload.message,
            msg_type=MessageType.HUMAN
        )

        # 4. Configura la memoria per questa conversazione specifica. Usiamo il context manager per ottenere il checkpointer asincrono
        async with get_checkpointer() as checkpointer:

            config = {"configurable": {"thread_id": thread_id}} #TODO: str(thread_uuid)
            inputs = {"messages": [("user", payload.message)]}


            # 5. Costruisci il grafo per questa richiesta
            try:
                graph = build_team_graph(
                    db=db,
                    team_id=payload.team_id,
                    checkpointer=checkpointer
                )
            except ValueError as e:
                print(f"Errore compilazione grafo: {e}")
                raise HTTPException(status_code=500, detail="Errore nella costruzione del team")


            # 5. Funzione generatrice per lo streaming
            async def generate_events():
                print("--- INIZIO STREAM ---")  # Debug
                final_message_to_save = None    # Variabile "buffer" per ricordare l'ultimo messaggio AI valido visto

                try:
                    # tramite astream generiamo flusso di eventi per ogni modifica nello stato del Grafo (fra cui la risposta man mano prodotta dall'agente)
                    async for event in graph.astream(inputs, config=config, stream_mode="values"):

                        # filtriamo gli eventi per mostrare solo la risposta dell'agente
                        if "messages" in event:
                            last_msg = event["messages"][-1]
                            last_msg.pretty_print()
                            if last_msg.type == "ai":
                                final_message_to_save = last_msg    # Alla fine del loop, avremo l'ultimo vero messaggio.
                                raw_content = last_msg.content
                                if isinstance(raw_content, list):
                                    content = "".join(str(item) for item in raw_content)
                                else:
                                    content = str(raw_content)
                                content = content.replace("\n", "\\n")
                                if content:
                                    yield f"data: {content}\n\n"   # formato Server-Sent Events (SSE) per notificare al Frontend di prendere il contenuto e aggiungerlo alla chat

                    # 6. Salvataggio risposta Team.
                    if final_message_to_save:
                        final_content = final_message_to_save.content
                        if isinstance(final_content, list):
                            final_content = "".join(str(item) for item in final_content)
                        # Pulizia ID LangChain
                        clean_id = clean_langchain_id(getattr(final_message_to_save, 'id', None))
                        message_db.add_message(
                            db=db,
                            id=clean_id,
                            thread_id=thread_id,
                            content=str(final_content),
                            msg_type=MessageType.AI,
                        )


                except Exception as e:
                    # Cattura errori DENTRO il generatore, altrimenti FastAPI li nasconde
                    print(f"ERRORE NEL GENERATORE: {e}")
                    yield f"data: Errore interno: {str(e)}\n\n"

            # il media_type="text/event-stream permette di non inviare un singolo json statico e quindi di non chiudere la connessione HTTP ad ogni yield, ma mantenerla aperta
            return StreamingResponse(generate_events(), media_type="text/event-stream")

    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Errore esecuzione: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("", response_model=list[ChatThreadRead])
async def read_all_chats(db: Session = Depends(get_db)):
    """
    Ottiene la lista di tutte le chat avviate dall'utente
    """

    try:
        return thread_service.get_chats_list(db=db)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(thread_id: str,
                 db: Session = Depends(get_db)):
    """
    Cancella il thread con id specificato dal sistema
    """
    try:
        thread_service.delete_thread(db=db, thread_id=thread_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))