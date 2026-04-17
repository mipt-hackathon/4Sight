import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class MlApiClientError(Exception):
    def __init__(self, error_code: str, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code


class MlApiClient:
    def __init__(self, http_client: httpx.Client) -> None:
        self._http_client = http_client

    def predict_churn(self, user_id: int) -> dict[str, Any]:
        return self._post_json("/ml/churn/predict", {"user_id": str(user_id)})

    def predict_recommendations(self, user_id: int, limit: int) -> dict[str, Any]:
        return self._post_json(
            "/ml/recommendations/predict",
            {"user_id": str(user_id), "limit": limit},
        )

    def predict_forecast(self, entity_id: str, horizon_days: int) -> dict[str, Any]:
        return self._post_json(
            "/ml/forecast/predict",
            {"entity_id": entity_id, "horizon_days": horizon_days},
        )

    def predict_segmentation(self, user_id: int) -> dict[str, Any]:
        return self._post_json("/ml/segmentation/predict", {"user_id": str(user_id)})

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._http_client.post(path, json=payload)
        except httpx.HTTPError as exc:
            raise MlApiClientError("UPSTREAM_UNAVAILABLE", str(exc)) from exc

        try:
            body = response.json()
        except ValueError as exc:
            raise MlApiClientError(
                "INVALID_RESPONSE",
                f"ML API returned non-JSON response for {path}",
                response.status_code,
            ) from exc

        if response.status_code != 200 or body.get("status") != "ok":
            payload_body = body.get("payload") if isinstance(body, dict) else None
            error_code = "UPSTREAM_ERROR"
            error_message = f"ML API returned HTTP {response.status_code}"
            if isinstance(payload_body, dict):
                error_code = str(payload_body.get("error_code") or error_code)
                error_message = str(payload_body.get("error_message") or error_message)
            logger.warning(
                "ML API request failed path=%s status_code=%s error_code=%s",
                path,
                response.status_code,
                error_code,
            )
            raise MlApiClientError(error_code, error_message, response.status_code)

        payload_body = body.get("payload")
        if not isinstance(payload_body, dict):
            raise MlApiClientError(
                "INVALID_RESPONSE",
                f"ML API returned invalid payload for {path}",
                response.status_code,
            )
        return payload_body
