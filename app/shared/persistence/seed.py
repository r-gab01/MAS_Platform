from sqlalchemy.orm import Session
from app.shared.persistence.models import LLMModel, PromptModel


def seed_llm_models(db: Session):
    """Popola il DB con i modelli di default se non esistono."""

    # Se ci sono già modelli, non fare nulla
    if db.query(LLMModel).first():
        return

    print("🌱 Seeding dei modelli LLM iniziali...")

    initial_models = [
        LLMModel(
            name="Sonnet 4.5",
            api_model_name="anthropic.claude-sonnet-4-5-20250929-v1:0",
            provider="aws",
        ),
        LLMModel(
            name="Nova Micro",
            api_model_name="amazon.nova-micro-v1:0",
            provider="aws",
        ),
        LLMModel(
            name="Nova Pro",
            api_model_name="amazon.nova-pro-v1:0",
            provider="aws",
        ),
        LLMModel(
            name="Llama 3.2-1B",
            api_model_name="meta.llama3-2-1b-instruct-v1:0",
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
            system_prompt="Sei un assistente esperto nella generazione di contenuti per ebook su Praga. "
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
                          "Procedi in questo modo: scrivi prima tutti i capitoli e poi generali ad uno uno. "
                          "Una volta ottenuti tutti i capitoli completi, il tuo compito finale è presentare l'intero ebook in formato markdown senza sintetizzare nulla. "
                          "Scrivi solo il contenuto dell'ebook"
        )
    ]
    db.add_all(initial_models)
    db.commit()