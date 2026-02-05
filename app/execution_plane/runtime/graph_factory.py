# La logica per costruire l'agente/team su richiesta.
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session


from app.shared.persistence.models import AgentModel, TeamModel
from app.shared.tools import toolFactory

from app.shared.persistence import team_db
from app.shared.factories import LLMFactory
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.agents.middleware import SummarizationMiddleware

class GraphFactory:

    @staticmethod
    def _create_worker_as_tool(worker: AgentModel):
        """
        Crea un tool che, quando chiamato, invoca l'agente worker.
        """
        # 1. Crea il modello e l'agente worker
        model = LLMFactory.get_llm_model(
            provider=worker.llm_model.provider,
            model_name=worker.llm_model.api_model_name,
            temperature=worker.temperature,
            max_tokens=None
        )

        worker_tools = []
        # Creazione Tools dell'agente
        for tool_used in worker.tools:
            try:
                tool_instance = toolFactory.create_tool(tool_used.name)
                worker_tools.append(tool_instance)
            except ValueError as e:
                print(f"Errore creazione tool {tool_used.name}: {e}")

        # Creazione tool per RAG con KnowledgeBases
        for kb in worker.knowledge_bases:
            try:
                kb_tool_instance = toolFactory.create_rag_tool(kb.id, kb.description)
                worker_tools.append(kb_tool_instance)
            except ValueError as e:
                print(f"Errore creazione kb {kb.id}: {e}")

        # Supponiamo che create_agent restituisca un Runnable/Graph compilato
        worker_agent = create_agent(
            model=model,
            system_prompt=worker.prompt.system_prompt if worker.prompt else None,
            tools=worker_tools,
        )

        # 2. Avvolgi l'agente in un Tool
        # Usiamo una closure per catturare l'agente specifico: ossia una funzione che mantiene l'accesso alle variabili dell'ambiente in cui è stata creata, anche dopo che quell'ambiente non esiste più.
        # Questo ci permette di accedere all'agente e richiamarlo. In altri modi perderemmo il riferimento all'agente e non potremmo chiamarlo più.
        @tool(simple_format(worker.name), description=worker.description)
        def call_worker_agent(query: str) -> str:
            """Delega il task all'agente specifico."""
            response = worker_agent.invoke({"messages": [HumanMessage(content=query)]})
            return response["messages"][-1].content

        return call_worker_agent    # questa funzione che restituisco (la closure) avrà riferimento a quell'agente e potrò usarla per richiamare l'agente in futuro


    @staticmethod
    def build_team_graph(db: Session, team_id: int, checkpointer=None):
        """
        Costruisce il grafo del team caricando i dati dal DB al volo.
        """
        # 1. Carico la configurazione del team dal Persistence Plane
        team : TeamModel = team_db.get_team_by_id(db, team_id)

        if not team:
            raise ValueError(f"Team con id='{team_id}' non trovato")

        # 2. Costruisco ogni worker come tool per il supervisor
        tools = []
        for worker in team.workers:
            worker_tool = GraphFactory._create_worker_as_tool(worker)
            tools.append(worker_tool)

        # 3. Crea il modello LLM del Supervisor
        supervisor_model = LLMFactory.get_llm_model(
            provider=team.supervisor.llm_model.provider,
            model_name=team.supervisor.llm_model.api_model_name,
            temperature=team.supervisor.temperature,
            max_tokens=None
        )

        # 4. Aggiungo Basi di conoscenza al supervisor
        for kb in team.supervisor.knowledge_bases:
            try:
                kb_tool_instance = toolFactory.create_rag_tool(kb.id, kb.description)
                tools.append(kb_tool_instance)
            except ValueError as e:
                print(f"Errore creazione kb {kb.id}: {e}")


        # 5. Creo l'agente Supervisor. Il supervisor ha accesso ai workers come tool
        supervisor_graph = create_agent(
            model=supervisor_model,
            system_prompt=team.supervisor.prompt.system_prompt if team.supervisor.prompt else None,
            tools=tools,
            middleware=[
                SummarizationMiddleware(
                    model= LLMFactory.get_llm_model(provider="aws-converse", model_name="eu.amazon.nova-micro-v1:0"),
            #        max_tokens_before_summary=4000,
                    messages_to_keep=3
                )
            ],
            checkpointer=checkpointer # memoria della chat!
        )

        return supervisor_graph


def simple_format(text: str) -> str:
    # "Ciao Mondo" -> "Ciao_Mondo"
    return text.strip().replace(" ", "_")


