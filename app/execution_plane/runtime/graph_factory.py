# La logica per costruire l'agente/team su richiesta.
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from app.shared.persistence.models import AgentModel, TeamModel

from app.shared.persistence import team_db
from app.shared.factories.llm_factory import get_llm_model
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.agents.middleware import SummarizationMiddleware

# WebSearch
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools import DuckDuckGoSearchRun

from app.shared.security.credential_manager import credential_manager


def _create_worker_tool(worker: AgentModel):
    """
    Crea un tool che, quando chiamato, invoca l'agente worker.
    """
    # 1. Crea il modello e l'agente worker
    model = get_llm_model(
        provider=worker.llm_model.provider,
        model_name=worker.llm_model.api_model_name,
        temperature=worker.temperature,
        max_tokens=None
    )

    # Supponiamo che create_agent restituisca un Runnable/Graph compilato
    worker_agent = create_agent(
        model=model,
        system_prompt=worker.prompt.system_prompt
    )

    # 2. Avvolgi l'agente in un Tool
    # Usiamo una closure per catturare l'agente specifico: ossia una funzione che mantiene l'accesso alle variabili dell'ambiente in cui è stata creata, anche dopo che quell'ambiente non esiste più.
    # Questo ci permette di accedere all'agente e richiamarlo. In altri modi perderemmo il riferimento all'agente e non potremmo chiamarlo più.
    @tool(worker.name, description=worker.description)
    def call_worker_agent(query: str) -> str:
        """Delega il task all'agente specifico."""
        response = worker_agent.invoke({"messages": [HumanMessage(content=query)]})
        return response["messages"][-1].content

    return call_worker_agent    # questa funzione che restituisco (la closure) avrà riferimento a quell'agente e potrò usarla per richiamare l'agente in futuro



def build_team_graph(db: Session, team_id: int, checkpointer=None):
    """
    Costruisce il grafo del team caricando i dati dal DB al volo.
    """
    # 1. Carico la configurazione del team dal Persistence Plane
    team : TeamModel = team_db.get_team_by_id(db, team_id)

    if not team:
        raise ValueError(f"Team con id='{team_id}' non trovato")

    # 2. Costruisco il tool per ogni worker
    tools = []
    for worker in team.workers:
        worker_tool = _create_worker_tool(worker)
        tools.append(worker_tool)

    # 3. Crea il Supervisor
    supervisor_model = get_llm_model(
        provider=team.supervisor.llm_model.provider,
        model_name=team.supervisor.llm_model.api_model_name,
        temperature=team.supervisor.temperature,
        max_tokens=None
    )

    # Il supervisor è un agente che ha accesso ai tool dei worker
    supervisor_graph = create_agent(
        model=supervisor_model,
        system_prompt=team.supervisor.prompt.system_prompt,
        tools=tools,
        middleware=[
            SummarizationMiddleware(
                model=get_llm_model(provider="aws-converse", model_name="eu.amazon.nova-micro-v1:0"),
        #        max_tokens_before_summary=4000,
                messages_to_keep=3
            )
        ],
        checkpointer=checkpointer # memoria della chat!
    )

    return supervisor_graph


def create_web_search_tool(deep=3):
    """
        Restituisce l'istanza del tool WebSearch con TavilySearch e DuckDuckGo configurata.
    """
    tavily_key = credential_manager.get_tavily_api_key()

    if tavily_key:
        return TavilySearchResults(
            max_results=3,
            tavily_api_key=tavily_key,
            description="Un motore di ricerca ottimizzato per ottenere informazioni attuali, news e dati specifici dal web."
        )

    # 2. Fallback: DuckDuckGo (Gratis, nessuna key necessaria)
    else:
        print("⚠️ Tavily Key non trovata. Uso DuckDuckGo per la ricerca.")
        return DuckDuckGoSearchRun(
            description="Un motore di ricerca web per trovare informazioni generali."
        )