from typing import Any

from pydantic import BaseModel, Field


class StubPredictionResponse(BaseModel):
    status: str
    request_type: str
    todo: str
    payload: dict[str, Any]
    trace_payload: dict[str, Any] | None = None


class ModelRoutingOptions(BaseModel):
    model_key: str | None = Field(default=None)
    model_version: str | None = Field(default=None)


class BaseMLRequest(BaseModel):
    options: ModelRoutingOptions | None = Field(default=None)
