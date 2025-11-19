from pydantic import BaseModel, Field

from app.shared.schemas.llm_model_schemas import LLMModelRead
from app.shared.schemas.prompt_schemas import PromptRead
from typing import Optional
import enum


class AgentType(str, enum.Enum):
    SUPERVISOR = "supervisor"
    WORKER = "worker"

# Schema di base (campi comuni)
class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Nome dell'agent")
    description: str = Field(..., description="Descrizione del team")
    prompt_id: int = Field(..., gt=0, description="ID del prompt da associare")
    model_deployment_id: int = Field(..., gt=0, description="ID del modello LLM da associare")
    temperature: float = Field(0.0, ge=0.0, le=1.0, description="Temperatura del modello LLM")
    agent_type: AgentType = AgentType.WORKER
    # Qui aggiungerai gli ID delle relazioni, es:
    # tool_names: List[str] = []
    # kb_ids: List[int] = []

# Schema per la CREAZIONE (ciò che riceviamo dal frontend)
class AgentCreate(AgentBase):
    pass  # Per ora, è uguale alla base

# Schema per la LETTURA (ciò che restituiamo, include l'ID del DB)
class AgentRead(AgentBase):
    id: int
    prompt: PromptRead  # Include i dettagli del prompt
    llm_model: LLMModelRead # Include i dettagli del LLM utilizzato

    class Config:
        from_attributes = True  # Questo dice a Pydantic di leggere i dati da un modello SQLAlchemy
                                # quindi pydantic per il campo id di AgentRead, legge created_agent.id etc. e crea AgentRead