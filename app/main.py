from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.shared.persistence.db_client import create_db_and_tables, SessionLocal
from app.shared.persistence.seed import seed_llm_models, seed_prompts, seed_agents, seed_tools
from app.shared.factories.checkpointer_factory import CheckpointFactory
from app.shared.factories.vector_store_factory import VectorStoreFactory
from app.control_plane.routes import (
    agents,
    prompts,
    teams,
    llm_models,
    knowledge_bases,
    tools
)
from app.execution_plane.routes import threads


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestore unificato del ciclo di vita dell'applicazione.
    Esegue in sequenza le operazioni sincrone (DB Setup) e asincrone (Pool Init).
    """

    # --- FASE 1: STARTUP SINCRONO (DB SQL) ---
    print("🔧 [Startup] 1/3: Verifica schema Database...")
    create_db_and_tables()

    print("🌱 [Startup] 2/3: Seeding dati iniziali...")
    db = SessionLocal()
    try:
        # Popoliamo il DB se necessario
        seed_llm_models(db)
        seed_prompts(db)
        seed_agents(db)
        seed_tools(db)
    except Exception as e:
        print(f"⚠️ Errore durante il seeding (non bloccante): {e}")
    finally:
        db.close()

    # --- FASE 2: STARTUP ASINCRONO (Pool LangGraph) ---
    print("🚀 [Startup] 3/3: Inizializzazione Connection Pool Async...")
    await CheckpointFactory.initialize()

    # (Opzionale) Pre-warm dell'engine vettoriale se vuoi che sia pronto subito
    # VectorStoreFactory.get_engine()

    print("✅ Sistema pronto.")

    yield  # L'applicazione resta sospesa qui quando gira

    # --- FASE 3: SHUTDOWN ---
    print("🛑 [Shutdown] Chiusura risorse...")
    await CheckpointFactory.close()
    VectorStoreFactory.dispose()  # Chiude l'engine dei vettori se presente


def create_app() -> FastAPI:
    """
    Costruisce l'applicazione unica.
    """
    application = FastAPI(
        title="AI Enterprise RAG Platform",
        description="Unified API for Control Plane (Management) and Execution Plane (Runtime)",
        version="1.0.0",
        lifespan=lifespan
    )

    # --- MIDDLEWARE ---
    # Fondamentale unificarlo qui per evitare problemi di CORS tra porte diverse
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In produzione: ["http://localhost:3000", "https://mia-app.com"]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- ROUTERS: CONTROL PLANE ---
    # Usiamo prefissi per tenere ordinata la documentazione Swagger
    cp_prefix = "/api/v1/control"

    application.include_router(teams.router, prefix=f"{cp_prefix}/teams", tags=["Control Plane - Teams"])
    application.include_router(agents.router, prefix=f"{cp_prefix}/agents", tags=["Control Plane - Agents"])
    application.include_router(tools.router, prefix=f"{cp_prefix}/tools", tags=["Control Plane - Tools"])
    application.include_router(prompts.router, prefix=f"{cp_prefix}/prompts", tags=["Control Plane - Prompts"])
    application.include_router(llm_models.router, prefix=f"{cp_prefix}/llm", tags=["Control Plane - LLM Models"])
    application.include_router(knowledge_bases.router, prefix=f"{cp_prefix}/kb", tags=["Control Plane - Knowledge Bases"])

    # --- ROUTERS: EXECUTION PLANE ---
    # La chat e i thread operativi
    ep_prefix = "/api/v1/execution"

    # Nota: Ho messo threads qui, assumendo sia la parte operativa (chat)
    application.include_router(threads.router, prefix=f"{ep_prefix}/threads", tags=["Execution Plane - Chat Threads"])

    # --- HEALTH CHECKS ---
    @application.get("/health", tags=["System"])
    def health_check():
        return {
            "status": "healthy",
            "components": {
                "database": "connected",  # Si potrebbe fare un vero check qui
                "checkpoint_pool": "active"  # Idem
            }
        }

    @application.get("/", tags=["System"])
    def root():
        return {"message": "AI RAG Platform API is running. Go to /docs for Swagger UI."}

    return application


# L'oggetto 'app' esposto per Uvicorn
app = create_app()

if __name__ == "__main__":
    import uvicorn

    # Avvia su tutte le interfacce, porta 8000
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)