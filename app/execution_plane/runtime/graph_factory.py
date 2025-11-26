# La logica per costruire l'agente/team su richiesta.
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from app.shared.persistence.models import AgentModel, TeamModel

from app.shared.persistence import team_db
from app.shared.factories.llm_factory import get_llm_model
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.agents.middleware import SummarizationMiddleware


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

    # 2. Costruisco i tool per ogni worker
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


"""
class TeamBuilder:
    '''Registry per gestire team, agenti e tool'''

    def __init__(self):
        self._agents = {}
        self._tools = {}
        self._teams = {}


    def build_agent_tool(self, team_model: TeamModel):
        '''
        Registra tutti i worker di un team come agenti e tool.
        '''
        workers = team_model.workers
        if not workers:
            return None

        for worker in workers:
            # Creo il model e il relativo agent per questo worker
            model = get_azure_model(worker.model_deployment, worker.temperature)
            agent = create_agent(model=model, system_prompt=worker.prompt.system_prompt, name=worker.name)

            @tool(worker.name, description=worker.description)
            def call_agent(argument: str) -> str:
                result = agent.invoke({"messages": [{"role": "user", "content": argument}]})
                return result["messages"][-1].content

            # Salva nel registry
            self._agents[worker.name] = agent
            self._tools[worker.name] = call_agent

            print(f"✓ Agente '{worker.name}' registrato con successo")
            yield agent, call_agent


    def register_team(self, team_model: TeamModel):
        '''Crea un team supervisor con gli agenti specificati'''

        # Verifica che tutti gli agenti richiesti esistano
        missing = [worker.name for worker in team_model.workers if worker.name not in self._tools]
        if missing:
            raise ValueError(f"Agenti non trovati: {missing}")

        # Raccogli i tool degli agenti
        team_tools = [self._tools[name] for name in team_model.workers]

        # Crea il modello del supervisor
        supervisor = team_model.supervisor
        model = get_azure_model(supervisor.model_deployment, supervisor.temperature)

        team = create_agent(
            model=model,
            system_prompt=supervisor.prompt.system_prompt,
            tools=team_tools
        )

        self._teams[team_model.name] = team
        print(f"✓ Team '{team_model.name}' creato con {len(team_tools)} agenti")
        return team
"""
