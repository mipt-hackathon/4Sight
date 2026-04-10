import logging
from typing import Any


def log_inference_result(logger: logging.Logger, use_case: str, latency_ms: int, outcome: str) -> None:
    logger.info("use_case=%s latency_ms=%d outcome=%s", use_case, latency_ms, outcome)


def log_feature_source(logger: logging.Logger, use_case: str, source: str) -> None:
    logger.debug("use_case=%s feature_source=%s", use_case, source)


def log_features_not_found(logger: logging.Logger, use_case: str) -> None:
    logger.warning("use_case=%s features_not_found", use_case)
