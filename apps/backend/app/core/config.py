from common.config import AppSettings, get_settings


def get_backend_settings() -> AppSettings:
    return get_settings()
