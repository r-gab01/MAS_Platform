from sqlalchemy.orm import Session
from app.shared.persistence.models import LLMModel, PromptModel, AgentModel, ToolModel
from app.shared.schemas.agent_schemas import AgentType


def seed_llm_models(db: Session):
    """Popola il DB con i modelli di default se non esistono."""

    # Se ci sono già modelli, non fare nulla
    if db.query(LLMModel).first():
        return

    print("🌱 Seeding dei modelli LLM iniziali...")

    initial_models = [
        LLMModel(
            name="Sonnet 4.5",
            api_model_name="eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
            provider="aws",
        ),
        LLMModel(
            name="Nova Micro",
            api_model_name="eu.amazon.nova-micro-v1:0",
            provider="aws",
        ),
        LLMModel(
            name="Nova Pro",
            api_model_name="eu.amazon.nova-pro-v1:0",
            provider="aws",
        ),
        LLMModel(
            name="Llama 3.2-1B",
            api_model_name="eu.meta.llama3-2-1b-instruct-v1:0",
            provider="aws",
        )
    ]

    db.add_all(initial_models)
    db.commit()



def seed_prompts(db: Session):
    """Popola il DB con dei prompt di default se non esistono."""

    # Se ci sono già modelli, non fare nulla
    if db.query(PromptModel).first():
        return

    print("🌱 Seeding dei prompt iniziali...")

    initial_models = [
        PromptModel(
            name="chapter_writer_prompt",
            description="Prompt per generare un capitolo ebook relativo ad un argomento",
            system_prompt="Sei un assistente esperto nella generazione di contenuti per ebook. "
                          "Il tuo unico compito è prendere un titolo di un capitolo fornito dall'utente e generare il capitolo relativo all'argomento, per un ebook. "
                          "Il capitolo generato deve essere esaustivo sull'argomento. Rispondi SOLO con il paragrafo generato."
        ),
        PromptModel(
            name="index_generator_prompt",
            description="Prompt per generare un elenco di capitoli",
            system_prompt="Sei un assistente esperto nella strutturazione di contenuti. "
                          "Il tuo unico compito è prendere un argomento fornito dall'utente e restituire un elenco puntato di capitoli per un ebook su quell'argomento. "
                          "Rispondi SOLO con l'elenco dei capitoli, nient'altro."
        ),
        PromptModel(
            name="ebook_supervisor_prompt",
            description="Prompt per gestire la creazione di un ebook",
            system_prompt="Sei un agente supervisore per la scrittura di ebook. "
                          "Il tuo compito è coordinare il processo di scrittura. "
                          "Procedi in questo modo: scrivi prima tutti i capitoli e poi generali ad uno uno tramite tools. Ricordati di fornire il contesto della richiesta dell'utente al tool. "
                          "Una volta ottenuti tutti i capitoli completi, il tuo compito finale è presentare l'intero ebook in formato markdown senza sintetizzare nulla. "
                          "Scrivi solo il contenuto dell'ebook"
        )
    ]
    db.add_all(initial_models)
    db.commit()

def seed_agents(db: Session):
    """
    Popola il DB con agenti starter
    """

    if db.query(AgentModel).first():
        return

    initial_models = [
        AgentModel(
            name="chapter_writer_agent",
            description="Agente in grado di scrivere un intero capitolo a partire da un titolo",
            temperature=0,
            agent_type=AgentType.WORKER,
            prompt_id=1,
            llm_model_id=2
        ),
        AgentModel(
            name="index_generator_agent",
            description="Agente in grado di redirre un indice di un ebook su un argomento",
            temperature=0,
            agent_type=AgentType.WORKER,
            prompt_id=2,
            llm_model_id=2
        ),
        AgentModel(
            name="ebook_supervisor",
            description="Supervisore nella scrittura di un ebook",
            temperature=0,
            agent_type=AgentType.WORKER,
            prompt_id=3,
            llm_model_id=2
        )
    ]
    db.add_all(initial_models)
    db.commit()


def seed_tools(db: Session):
    """Popola il catalogo dei tool disponibili."""

    # Definisci i tool del tuo sistema
    available_tools = [
            {
                "name": "web_search",
                "display_name": "Ricerca Web (Tavily)",
                "description": "Permette all'agente di cercare informazioni in tempo reale su internet."
            }
        ]

    for tool_data in available_tools:
        exists = db.query(ToolModel).filter(ToolModel.name == tool_data["name"]).first()
        if not exists:
            new_tool = ToolModel(**tool_data)
            db.add(new_tool)

    db.commit()
    print("🌱 Seeding dei tool...")