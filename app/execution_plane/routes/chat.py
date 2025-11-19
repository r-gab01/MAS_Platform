# API: /api/v1/chat/{team_id} (POST per avviare/continuare la chat)

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.execution_plane.runtime.graph_factory import build_team_graph
from app.shared.persistence.db_client import get_db

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat Execution"]
)

# Schema di input semplice
class ChatRequest(BaseModel):
    message: str
    thread_id: str  # questo parametro permette di identificare la sessione utente e mantenere la memoria


@router.post("/{team_id}")
async def chat_stream(
        team_id: int,           # id del team con cui chattare
        payload: ChatRequest,   # contenuto inviato di tipo ChatRequest
        db: Session = Depends(get_db)   # collegamento al db
):
    """
    Esegue una chat con un team specifico.
    Restituisce una risposta in streaming (Server-Sent Events).
    """

    try:
        # 1. Configura la memoria per questa conversazione specifica
        # checkpointer = get_checkpointer() # Configurato su Postgres/Redis

        # 2. Costruisci il grafo per questa richiesta
        graph = build_team_graph(db=db, team_id=team_id)  # , checkpointer=checkpointer)

        # 3. Configurazione di esecuzione
        config = {"configurable": {"thread_id": payload.thread_id}}
        inputs = {"messages": [("user", payload.message)]}

        # 4. Funzione generatrice per lo streaming
        async def generate_events():
            # tramite astram generiamo flusso di eventi per ogni modifica nello stato del Grafo (fra cui la risposta man mano prodotta dall'agente)
            async for event in graph.astream(inputs, config=config):
                # filtriamo gli eventi per mostrare solo la risposta dell'agente
                if "messages" in event:
                    last_msg = event["messages"][-1]
                    if last_msg.type == "ai":
                        yield f"data: {last_msg.content}\n\n"   # formato Server-Sent Events (SSE) per notificare al Frontend di prendere il contenuto e aggiungerlo alla chat

        # il media_type="text/event-stream permette di non inviare un singolo json statico e quindi di non chiudere la connessione HTTP ad ogni yield, ma mantenerla aperta
        return StreamingResponse(generate_events(), media_type="text/event-stream")

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Errore esecuzione: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")