#TODO: Lettura chiavi da AWS Secrets Manager, db cifrato o qualsiasi altra soluzione pensata

#Confgiurazione per lettura chiavi da file .env
import os
from typing import Dict

class CredentialManager:
    """
    Gestisce il recupero sicuro delle credenziali per i vari provider.
    """

    def get_azure_credentials(self) -> Dict[str, str]:
        """Recupera credenziali per Azure OpenAI"""
        return {
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
            "embedding_deployment": os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        }

    def get_aws_credentials(self) -> Dict[str, str]:
        """
        Recupera credenziali per AWS Bedrock.
        Nota: In produzione su AWS, spesso non servono keys esplicite
        se usi IAM Roles, ma per sviluppo locale servono.
        """
        return {
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
            "region_name": os.getenv("AWS_REGION", "us-east-1"),
            "embedding_model_id": os.getenv("AWS_EMBEDDING_MODEL_ID")
        }

    def get_ollama_credentials(self) -> Dict[str, str]:

        return {
            "ollama_base_url": os.getenv("OLLAMA_BASE_URL")
        }

    def get_huggingface_credentials(self) -> Dict[str, str]:
        """
        Recupera credenziali per HuggingFace Locale.
        """


    def get_tavily_api_key(self) -> str:
        """
        Recuper api key per Tavily Search, usato per costruire web search tool
        """
        key = os.getenv("TAVILY_API_KEY")
        return key

# Istanza singleton
credential_manager = CredentialManager()
