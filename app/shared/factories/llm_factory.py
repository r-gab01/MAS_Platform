from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import AzureChatOpenAI
from langchain_aws import ChatBedrock, ChatBedrockConverse
from langchain_ollama import ChatOllama
from app.shared.security.credential_manager import credential_manager

from botocore.config import Config

class LLMFactory:
    """
    Factory centralizzata per istanziare modelli LLM da differenti provider.
    A partire da configurazione astratta (es. provider="aws", model="claude-3") restituisce
    l'oggetto LangChain corretto pronto all'uso.
    """

    @staticmethod
    def get_llm_model(
            provider: str,
            model_name: str,
            temperature: float = 0.0,
            max_tokens: int = None,
            callbacks: list = None
    ) -> BaseChatModel:
        """
        Factory che restituisce l'istanza LangChain corretta in base al provider.

        Args:
            provider: "azure", "aws", "openai"
            model_name: Il nome del deployment (Azure) o model ID (AWS/OpenAI)
            temperature: Creatività del modello
            max_tokens: numero di tokens massimo di output del modello
            callbacks: lista di callback da passare al modello
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
                max_tokens=max_tokens,
                callbacks=callbacks
            )

        # --- CASO 2: AWS BEDROCK CONVERSE (AMAZON MODELS)
        elif provider.lower() == "aws-converse":
            creds = credential_manager.get_aws_credentials()

            return ChatBedrockConverse(
                model_id=model_name,  # es. "anthropic.claude-3-sonnet-20240229-v1:0"
                client=None,  # LangChain creerà il client boto3 automaticamente
                region_name=creds["region_name"],
                aws_access_key_id=creds["aws_access_key_id"],
                aws_secret_access_key=creds["aws_secret_access_key"],
                #model_kwargs={"temperature": temperature}  # Bedrock passa i param così
                temperature=temperature,
                max_tokens=max_tokens,
                callbacks=callbacks
            )

        # --- CASO 3: AWS BEDROCK (Claude, Llama, Titan) ---
        elif provider.lower() == "aws":
            creds = credential_manager.get_aws_credentials()

            return ChatBedrock(
                model_id=model_name,  # es. "anthropic.claude-3-sonnet-20240229-v1:0"
                client=None,  # LangChain creerà il client boto3 automaticamente
                region_name=creds["region_name"],
                aws_access_key_id=creds["aws_access_key_id"],
                aws_secret_access_key=creds["aws_secret_access_key"],
                model_kwargs={
                    "temperature": temperature,
                    "max_tokens": 32000  # Sonnet 4.5 supporta fino a 64k in output
                },
                config=Config(
                    read_timeout=600,  # 600 secondi = 10 minuti
                    connect_timeout=10,
                    retries={
                        'max_attempts': 3,
                        'mode': 'standard'
                    }
                ),
                callbacks=callbacks
            )

        # --- CASO 3: OLLAMA (loal)
        elif provider.lower() == "local":
            creds = credential_manager.get_ollama_credentials()
            if not creds["ollama_base_url"]:
                raise ValueError("local API Key mancante")

            return ChatOllama(
                model=model_name,
                temperature=temperature,
                base_url=creds.get("ollama_base_url")
            )


        else:
            raise ValueError(f"Provider '{provider}' non supportato.")