from fastapi import APIRouter, Depends

from app.api.models import SupersetDeepDiveEmbedResponse
from app.dependencies import get_superset_embed_service
from app.services.superset_embed_service import SupersetEmbedService

router = APIRouter()


@router.get("/deep-dive/embed", response_model=SupersetDeepDiveEmbedResponse)
def get_deep_dive_embed(
    service: SupersetEmbedService = Depends(get_superset_embed_service),
) -> SupersetDeepDiveEmbedResponse:
    return service.get_deep_dive_embed()
