import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    DEFAULT_CATALOG_URL: str = os.getenv("CATALOG_SERVICE_URL", "http://127.0.0.1:8000")
    DEFAULT_DOCUMENT_URL: str = os.getenv("DOCUMENT_SERVICE_URL", "http://127.0.0.1:8001")
    APP_TITLE: str = "Business Mention Resolution Platform"
    APP_ICON: str = "🏢"
    PAGE_LAYOUT: str = "wide"
    DEFAULT_PAGE_SIZE: int = 15
    REQUEST_TIMEOUT: float = 60.0
