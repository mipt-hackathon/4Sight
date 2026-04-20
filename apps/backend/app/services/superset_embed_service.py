from app.api.models import SupersetDeepDiveEmbedResponse
from app.core.config import BackendSettings
from app.integrations.superset_client import SupersetClient


class SupersetEmbedService:
    def __init__(
        self,
        superset_client: SupersetClient,
        settings: BackendSettings,
    ) -> None:
        self._superset_client = superset_client
        self._settings = settings

    def get_deep_dive_embed(self) -> SupersetDeepDiveEmbedResponse:
        allowed_domains = [
            domain.strip()
            for domain in self._settings.superset_embed_allowed_domains.split(",")
            if domain.strip()
        ]
        embedded_config = self._superset_client.get_or_create_embedded_dashboard(
            dashboard_slug=self._settings.superset_embed_dashboard_slug,
            allowed_domains=allowed_domains,
        )
        guest_token = self._superset_client.create_guest_token(
            embedded_dashboard_id=str(embedded_config["uuid"]),
            username=self._settings.superset_guest_username,
        )

        return SupersetDeepDiveEmbedResponse(
            dashboard_slug=self._settings.superset_embed_dashboard_slug,
            dashboard_title=self._settings.superset_embed_dashboard_title,
            dashboard_url=(
                f"{self._settings.superset_public_url.rstrip('/')}/superset/dashboard/"
                f"{self._settings.superset_embed_dashboard_slug}/"
            ),
            superset_domain=self._settings.superset_public_url.rstrip("/"),
            embedded_id=str(embedded_config["uuid"]),
            guest_token=guest_token,
        )
