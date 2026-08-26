"""Unified API client for Catalog and Document services with JWT authentication."""

import logging
from typing import Any, Dict, List, Optional, Tuple
import httpx

from frontend.config import AppConfig

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """Custom API exception containing response status code and detailed error message."""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class ApiClient:
    """Client for interacting with Business Mention Resolution Platform microservices."""

    def __init__(
        self,
        catalog_url: Optional[str] = None,
        document_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: float = AppConfig.REQUEST_TIMEOUT,
    ):
        self.catalog_url = (catalog_url or AppConfig.DEFAULT_CATALOG_URL).rstrip("/")
        self.document_url = (document_url or AppConfig.DEFAULT_DOCUMENT_URL).rstrip("/")
        self.token = token
        self.timeout = timeout

    def set_token(self, token: Optional[str]) -> None:
        """Update active JWT Bearer token."""
        self.token = token

    def _get_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if custom_headers:
            headers.update(custom_headers)
        return headers

    def _parse_error_detail(self, response: httpx.Response) -> str:
        try:
            data = response.json()
            if isinstance(data, dict):
                detail = data.get("detail")
                if isinstance(detail, list):
                    # Validation errors from FastAPI/Pydantic
                    messages = []
                    for err in detail:
                        loc = " -> ".join([str(x) for x in err.get("loc", []) if x != "body"])
                        msg = err.get("msg", "Invalid value")
                        messages.append(f"{loc}: {msg}" if loc else msg)
                    return "; ".join(messages)
                elif detail:
                    return str(detail)
                elif "message" in data:
                    return str(data["message"])
            return response.text or f"HTTP {response.status_code}"
        except Exception:
            return response.text or f"HTTP {response.status_code}"

    def _request(
        self,
        method: str,
        base_url: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout_override: Optional[float] = None,
    ) -> Any:
        url = f"{base_url}{path}"
        req_headers = self._get_headers(headers)
        timeout = timeout_override or self.timeout

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    data=data,
                    headers=req_headers,
                )

                if response.status_code >= 400:
                    error_msg = self._parse_error_detail(response)
                    raise ApiError(error_msg, status_code=response.status_code)

                if response.status_code == 204:
                    return None

                # Return JSON or empty dict
                try:
                    return response.json()
                except Exception:
                    return response.text

        except httpx.ConnectError:
            raise ApiError(f"Cannot connect to service at {base_url}. Is the service running?")
        except httpx.TimeoutException:
            raise ApiError(f"Request to {url} timed out after {timeout} seconds.")
        except ApiError:
            raise
        except Exception as e:
            raise ApiError(f"Unexpected error: {str(e)}")

    # ------------------------------------------------------------------
    # Health Checks
    # ------------------------------------------------------------------

    def check_catalog_health(self) -> Tuple[bool, str]:
        try:
            with httpx.Client(timeout=4.0) as client:
                r = client.get(f"{self.catalog_url}/")
                if r.status_code == 200:
                    return True, "Online"
                return False, f"HTTP {r.status_code}"
        except Exception as e:
            return False, f"Offline ({e.__class__.__name__})"

    def check_document_health(self) -> Tuple[bool, str]:
        try:
            with httpx.Client(timeout=4.0) as client:
                r = client.get(f"{self.document_url}/")
                if r.status_code == 200:
                    return True, "Online"
                return False, f"HTTP {r.status_code}"
        except Exception as e:
            return False, f"Offline ({e.__class__.__name__})"

    # ------------------------------------------------------------------
    # Auth Endpoints
    # ------------------------------------------------------------------

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user and obtain JWT access token."""
        return self._request(
            method="POST",
            base_url=self.catalog_url,
            path="/auth/login",
            data={"username": username, "password": password},
        )

    def register(self, username: str, password: str, role: str = "viewer") -> Dict[str, Any]:
        """Register a new user."""
        return self._request(
            method="POST",
            base_url=self.catalog_url,
            path="/auth/register",
            json_data={"username": username, "password": password, "role": role},
        )

    def get_me(self) -> Dict[str, Any]:
        """Fetch current authenticated user profile."""
        return self._request(
            method="GET",
            base_url=self.catalog_url,
            path="/auth/me",
        )

    # ------------------------------------------------------------------
    # Business Catalog Endpoints
    # ------------------------------------------------------------------

    def get_businesses(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        city: Optional[str] = None,
        category_id: Optional[int] = None,
        is_verified: Optional[bool] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        if city:
            params["city"] = city
        if category_id is not None:
            params["category_id"] = category_id
        if is_verified is not None:
            params["is_verified"] = is_verified

        return self._request(
            method="GET",
            base_url=self.catalog_url,
            path="/businesses",
            params=params,
        )

    def get_business(self, business_pk: int) -> Dict[str, Any]:
        return self._request(
            method="GET",
            base_url=self.catalog_url,
            path=f"/businesses/{business_pk}",
        )

    def create_business(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            method="POST",
            base_url=self.catalog_url,
            path="/businesses",
            json_data=data,
        )

    def update_business(self, business_pk: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            method="PUT",
            base_url=self.catalog_url,
            path=f"/businesses/{business_pk}",
            json_data=data,
        )

    def delete_business(self, business_pk: int) -> None:
        self._request(
            method="DELETE",
            base_url=self.catalog_url,
            path=f"/businesses/{business_pk}",
        )

    # ------------------------------------------------------------------
    # Categories Endpoints
    # ------------------------------------------------------------------

    def get_categories(
        self,
        page: int = 1,
        page_size: int = 100,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search

        return self._request(
            method="GET",
            base_url=self.catalog_url,
            path="/categories",
            params=params,
        )

    def create_category(self, name: str) -> Dict[str, Any]:
        return self._request(
            method="POST",
            base_url=self.catalog_url,
            path="/categories",
            json_data={"name": name},
        )

    def delete_category(self, category_id: int) -> None:
        self._request(
            method="DELETE",
            base_url=self.catalog_url,
            path=f"/categories/{category_id}",
        )

    # ------------------------------------------------------------------
    # Mentions Endpoints
    # ------------------------------------------------------------------

    def get_mentions(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        if status_filter and status_filter.lower() != "all":
            params["status_filter"] = status_filter

        return self._request(
            method="GET",
            base_url=self.catalog_url,
            path="/mentions",
            params=params,
        )

    def get_mention(self, mention_id: int) -> Dict[str, Any]:
        return self._request(
            method="GET",
            base_url=self.catalog_url,
            path=f"/mentions/{mention_id}",
        )

    def create_mention(
        self,
        text: str,
        source_text: Optional[str] = None,
        source_type: str = "review",
        source_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "text": text,
            "source_text": source_text,
            "source_type": source_type,
            "source_id": source_id,
        }
        return self._request(
            method="POST",
            base_url=self.catalog_url,
            path="/mentions",
            json_data=payload,
        )

    def delete_mention(self, mention_id: int) -> None:
        self._request(
            method="DELETE",
            base_url=self.catalog_url,
            path=f"/mentions/{mention_id}",
        )

    # ------------------------------------------------------------------
    # Resolution Endpoints
    # ------------------------------------------------------------------

    def resolve_mention(self, mention_id: int, max_candidates: int = 5) -> Dict[str, Any]:
        return self._request(
            method="POST",
            base_url=self.catalog_url,
            path=f"/resolution/mentions/{mention_id}",
            json_data={"max_candidates": max_candidates},
        )

    def smart_resolve_mention(self, mention_id: int, max_candidates: int = 5) -> Dict[str, Any]:
        return self._request(
            method="POST",
            base_url=self.catalog_url,
            path=f"/assistant/mentions/{mention_id}/resolve",
            json_data={"max_candidates": max_candidates},
            timeout_override=90.0,
        )

    def get_resolution_results(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        return self._request(
            method="GET",
            base_url=self.catalog_url,
            path="/resolution/results",
            params={"page": page, "page_size": page_size},
        )

    def get_review_queue(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        return self._request(
            method="GET",
            base_url=self.catalog_url,
            path="/resolution/review-queue",
            params={"page": page, "page_size": page_size},
        )

    def approve_resolution(self, result_id: int, notes: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if notes and notes.strip():
            payload["notes"] = notes.strip()
        return self._request(
            method="POST",
            base_url=self.catalog_url,
            path=f"/resolution/results/{result_id}/approve",
            json_data=payload,
        )

    def reject_resolution(self, result_id: int, notes: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if notes and notes.strip():
            payload["notes"] = notes.strip()
        return self._request(
            method="POST",
            base_url=self.catalog_url,
            path=f"/resolution/results/{result_id}/reject",
            json_data=payload,
        )

    # ------------------------------------------------------------------
    # Mention Extraction Endpoints
    # ------------------------------------------------------------------

    def extract_mentions(
        self,
        text: str,
        source_type: str = "review",
        source_id: Optional[str] = None,
        save_mentions: bool = True,
    ) -> Dict[str, Any]:
        payload = {
            "text": text,
            "source_type": source_type,
            "source_id": source_id,
            "save_mentions": save_mentions,
        }
        return self._request(
            method="POST",
            base_url=self.catalog_url,
            path="/extraction/mentions",
            json_data=payload,
        )

    # ------------------------------------------------------------------
    # Catalog QA Endpoints
    # ------------------------------------------------------------------

    def ask_catalog_question(self, question: str) -> Dict[str, Any]:
        return self._request(
            method="POST",
            base_url=self.catalog_url,
            path="/qa/ask",
            json_data={"question": question},
            timeout_override=45.0,
        )

    # ------------------------------------------------------------------
    # Document Service Endpoints (port 8001)
    # ------------------------------------------------------------------

    def get_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        document_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if document_type and document_type.lower() != "all":
            params["document_type"] = document_type

        return self._request(
            method="GET",
            base_url=self.document_url,
            path="/documents",
            params=params,
        )

    def get_document(self, document_id: int) -> Dict[str, Any]:
        return self._request(
            method="GET",
            base_url=self.document_url,
            path=f"/documents/{document_id}",
        )

    def generate_resolution_summary(self, mention_id: int) -> Dict[str, Any]:
        return self._request(
            method="POST",
            base_url=self.document_url,
            path=f"/documents/resolution-summary/{mention_id}",
        )

    def generate_monthly_report(self, month: str) -> Dict[str, Any]:
        return self._request(
            method="POST",
            base_url=self.document_url,
            path="/documents/monthly-report",
            json_data={"month": month},
        )

    def download_document(self, document_id: int) -> Tuple[bytes, str]:
        """Download a document PDF by document_id and return (bytes, filename)."""
        url = f"{self.document_url}/documents/{document_id}/download"
        headers = self._get_headers()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers)
                if response.status_code >= 400:
                    error_msg = self._parse_error_detail(response)
                    raise ApiError(error_msg, status_code=response.status_code)

                content_disp = response.headers.get("content-disposition", "")
                filename = f"document_{document_id}.pdf"
                if "filename=" in content_disp:
                    filename = content_disp.split("filename=")[-1].strip(' "')

                return response.content, filename
        except httpx.ConnectError:
            raise ApiError(f"Cannot connect to document service at {self.document_url}")
        except Exception as e:
            if isinstance(e, ApiError):
                raise
            raise ApiError(f"Failed to download document: {str(e)}")
