from langchain_core.embeddings import Embeddings
from langchain_openai import AzureOpenAIEmbeddings
from langchain_aws import BedrockEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from app.shared.security.credential_manager import credential_manager


class EmbeddingFactory:
    """
    Factory centralizzata per gli Embeddings.
    """

    @staticmethod  # metodo statico così è stateless, non ha parametri self della classe, non necessita oggetto istanziato e ogni chiamata istanzia nuovo embedder
    def get_embedding_model(
            provider: str,
    ) -> Embeddings:

        provider = provider.lower()

        # --- AZURE OPENAI ---
        if provider == "azure":
            creds = credential_manager.get_azure_credentials()
            if not creds["api_key"]:
                raise ValueError("Azure API Key mancante")

            return AzureOpenAIEmbeddings(
                azure_deployment=creds["embedding_deployment"],
                api_version=creds["api_version"],
                azure_endpoint=creds["endpoint"],
                api_key=creds["api_key"]
            )

        # --- AWS BEDROCK ---
        elif provider == "aws":
            creds = credential_manager.get_aws_credentials()

            return BedrockEmbeddings(
                model_id=creds["embedding_model_id"],
                client=None,  # Boto3 creato in automatico
                region_name=creds["region_name"],
                aws_access_key_id=creds["aws_access_key_id"],
                aws_secret_access_key=creds["aws_secret_access_key"]
            )

        # --- HUGGINGFACE ---
        elif provider == "huggingface":

            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            device = "cuda"

            return HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': device}
            )

        else:
            raise ValueError(f"Provider '{provider}' non supportato per Embeddings.")