import logging

logger = logging.getLogger(__name__)


def emit_counter(name: str, value: int = 1, **labels: str) -> None:
    """Placeholder metrics hook for future Prometheus/OTel integration."""

    logger.debug("metric=%s value=%s labels=%s", name, value, labels)
