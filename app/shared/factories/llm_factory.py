# Factory che a partire da configurazione astratta (es. provider="aws", model="claude-3") restituisce l'oggetto LangChain corretto pronto all'uso.

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import AzureChatOpenAI
from langchain_aws import ChatBedrock
from app.shared.security.credential_manager import credential_manager


def get_llm_model(
        provider: str,
        model_name: str,
        temperature: float = 0.0,
        max_tokens: int = None
) -> BaseChatModel:
    """
    Factory che restituisce l'istanza LangChain corretta in base al provider.

    Args:
        provider: "azure", "aws", "openai"
        model_name: Il nome del deployment (Azure) o model ID (AWS/OpenAI)
        temperature: Creatività del modello
        max_tokens: numero di tokens massimo di output del modello
    """

    # --- CASO 1: AZURE OPENAI ---
    if provider.lower() == "azure":
        creds = credential_manager.get_azure_credentials()
        if not creds["api_key"]:
            raise ValueError("Azure API Key mancante")

        return AzureChatOpenAI(
            azure_deployment=model_name,  # In Azure il 'model' è il nome del deployment
            api_version=creds["api_version"],
            azure_endpoint=creds["endpoint"],
            api_key=creds["api_key"],
            temperature=temperature,
            max_tokens=max_tokens
        )

    # --- CASO 2: AWS BEDROCK (Claude, Llama, Titan) ---
    elif provider.lower() == "aws":
        creds = credential_manager.get_aws_credentials()

        return ChatBedrock(
            model_id=model_name,  # es. "anthropic.claude-3-sonnet-20240229-v1:0"
            client=None,  # LangChain creerà il client boto3 automaticamente
            region_name=creds["region_name"],
            aws_access_key_id=creds["aws_access_key_id"],
            aws_secret_access_key=creds["aws_secret_access_key"],
            model_kwargs={"temperature": temperature}  # Bedrock passa i param così
        )

    else:
        raise ValueError(f"Provider '{provider}' non supportato.")