import logging
from collections.abc import Sequence
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


class SupersetClientError(Exception):
    def __init__(self, error_code: str, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code


class SupersetClient:
    def __init__(
        self,
        http_client: httpx.Client,
        username: str,
        password: str,
    ) -> None:
        self._http_client = http_client
        self._username = username
        self._password = password

    def get_or_create_embedded_dashboard(
        self,
        dashboard_slug: str,
        allowed_domains: Sequence[str],
    ) -> dict[str, Any]:
        access_token = self._login()
        csrf_token = self._get_csrf_token(access_token)
        quoted_slug = quote(dashboard_slug, safe="")
        path = f"/api/v1/dashboard/{quoted_slug}/embedded"

        response = self._request(
            "GET",
            path,
            access_token=access_token,
            expected_status_codes={200, 404},
        )
        if response.status_code == 404:
            response = self._request(
                "POST",
                path,
                access_token=access_token,
                csrf_token=csrf_token,
                json={"allowed_domains": list(allowed_domains)},
                expected_status_codes={200, 201},
            )
        else:
            result = self._extract_result(response)
            existing_domains = sorted(result.get("allowed_domains") or [])
            target_domains = sorted({domain for domain in allowed_domains if domain})
            if existing_domains != target_domains:
                response = self._request(
                    "PUT",
                    path,
                    access_token=access_token,
                    csrf_token=csrf_token,
                    json={"allowed_domains": target_domains},
                    expected_status_codes={200},
                )

        result = self._extract_result(response)
        embedded_uuid = result.get("uuid")
        if not embedded_uuid:
            raise SupersetClientError(
                "INVALID_RESPONSE",
                f"Superset did not return embedded UUID for dashboard '{dashboard_slug}'",
                response.status_code,
            )
        return result

    def create_guest_token(
        self,
        embedded_dashboard_id: str,
        *,
        username: str,
        first_name: str = "Retail",
        last_name: str = "Viewer",
    ) -> str:
        access_token = self._login()
        csrf_token = self._get_csrf_token(access_token)
        response = self._request(
            "POST",
            "/api/v1/security/guest_token/",
            access_token=access_token,
            csrf_token=csrf_token,
            json={
                "user": {
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                },
                "resources": [{"type": "dashboard", "id": embedded_dashboard_id}],
                "rls": [],
            },
            expected_status_codes={200},
        )
        body = response.json()
        token = body.get("token")
        if not token and isinstance(body.get("result"), dict):
            token = body["result"].get("token")
        if not token:
            raise SupersetClientError(
                "INVALID_RESPONSE",
                "Superset did not return guest token",
                response.status_code,
            )
        return str(token)

    def _login(self) -> str:
        response = self._request(
            "POST",
            "/api/v1/security/login",
            json={
                "username": self._username,
                "password": self._password,
                "provider": "db",
                "refresh": True,
            },
            expected_status_codes={200},
        )
        body = response.json()
        access_token = body.get("access_token")
        if not access_token:
            raise SupersetClientError(
                "INVALID_RESPONSE",
                "Superset did not return access token",
                response.status_code,
            )
        return str(access_token)

    def _get_csrf_token(self, access_token: str) -> str:
        response = self._request(
            "GET",
            "/api/v1/security/csrf_token/",
            access_token=access_token,
            expected_status_codes={200},
        )
        body = response.json()
        csrf_token = body.get("result")
        if not csrf_token:
            raise SupersetClientError(
                "INVALID_RESPONSE",
                "Superset did not return CSRF token",
                response.status_code,
            )
        return str(csrf_token)

    def _request(
        self,
        method: str,
        path: str,
        *,
        access_token: str | None = None,
        csrf_token: str | None = None,
        expected_status_codes: set[int],
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        headers: dict[str, str] = {"Accept": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        if csrf_token:
            headers["X-CSRFToken"] = csrf_token
            headers["Referer"] = str(self._http_client.base_url)

        try:
            response = self._http_client.request(
                method,
                path,
                headers=headers,
                json=json,
            )
        except httpx.HTTPError as exc:
            raise SupersetClientError("UPSTREAM_UNAVAILABLE", str(exc)) from exc

        if response.status_code not in expected_status_codes:
            body_text = response.text
            logger.warning(
                "Superset request failed method=%s path=%s status=%s body=%s",
                method,
                path,
                response.status_code,
                body_text[:500],
            )
            raise SupersetClientError(
                "UPSTREAM_ERROR",
                f"Superset returned HTTP {response.status_code} for {path}",
                response.status_code,
            )
        return response

    @staticmethod
    def _extract_result(response: httpx.Response) -> dict[str, Any]:
        body = response.json()
        result = body.get("result")
        if not isinstance(result, dict):
            raise SupersetClientError(
                "INVALID_RESPONSE",
                "Superset returned invalid result payload",
                response.status_code,
            )
        return result
