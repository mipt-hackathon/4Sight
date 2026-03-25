from common.config.settings import AppSettings, get_settings


def get_backend_settings() -> AppSettings:
    return get_settings()
