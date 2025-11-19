
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.execution_plane.routes import chat

# Factory function per creare l'app
def create_app():
    application = FastAPI(
        title="Agent Execution Plane",
        description="API Runtime per l'esecuzione dei team di agenti",
        version="1.0.0"
    )

    """
    # Configurazione CORS (Fondamentale se il frontend è su un'altra porta/dominio)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In produzione metti l'URL del frontend
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    """

    # Registrazione delle Routes
    application.include_router(chat.router)
    return application

app = create_app()