from datetime import datetime

from pydantic import BaseModel


class ModelVersionInfo(BaseModel):
    model_name: str
    model_version: str
    stage: str
    artifact_path: str
    is_active: bool
    created_at: datetime
