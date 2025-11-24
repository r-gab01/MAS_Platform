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

        # 2. Configurazione di esecuzione
        config = {"configurable": {"thread_id": payload.thread_id}}
        inputs = {"messages": [("user", payload.message)]}

        # 3. Costruisci il grafo per questa richiesta
        try:
            graph = build_team_graph(db=db, team_id=team_id)  # , checkpointer=checkpointer)
        except ValueError as e:
            raise HTTPException(status_code=500, detail="Impossibile Collegari al DB")



        # 4. Funzione generatrice per lo streaming
        async def generate_events():
            print("--- INIZIO STREAM ---")  # Debug
            try:

                # tramite astream generiamo flusso di eventi per ogni modifica nello stato del Grafo (fra cui la risposta man mano prodotta dall'agente)
                async for event in graph.astream(inputs, config=config, stream_mode="values"):

                    print(f"Evento ricevuto: {event.keys()}")
                    # filtriamo gli eventi per mostrare solo la risposta dell'agente
                    if "messages" in event:
                        last_msg = event["messages"][-1]
                        last_msg.pretty_print()
                        if last_msg.type == "ai":
                            raw_content = last_msg.content
                            if isinstance(raw_content, list):
                                content = "".join(str(item) for item in raw_content)
                            else:
                                content = str(raw_content)
                            content = content.replace("\n", "\\n")

                            yield f"data: {content}\n\n"   # formato Server-Sent Events (SSE) per notificare al Frontend di prendere il contenuto e aggiungerlo alla chat
                    """        
                    if "messages" in event and event["messages"]:
                        last_msg = event["messages"][-1]
                        last_msg.pretty_print()
                        yield f"data: {last_msg.content}\n\n"
                    """



            except Exception as e:
                # Cattura errori DENTRO il generatore, altrimenti FastAPI li nasconde
                print(f"ERRORE NEL GENERATORE: {e}")
                yield f"data: Errore interno: {str(e)}\n\n"

        # il media_type="text/event-stream permette di non inviare un singolo json statico e quindi di non chiudere la connessione HTTP ad ogni yield, ma mantenerla aperta
        return StreamingResponse(generate_events(), media_type="text/event-stream")

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Errore esecuzione: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")