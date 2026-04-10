from common.metrics.registry import emit_counter


def emit_request(use_case: str, outcome: str) -> None:
    emit_counter("ml.requests.total", 1, use_case=use_case, outcome=outcome)


def emit_business_error(use_case: str, error_type: str) -> None:
    emit_counter("ml.business_errors.total", 1, use_case=use_case, error_type=error_type)


def emit_model_error(use_case: str, error_type: str) -> None:
    emit_counter("ml.model_errors.total", 1, use_case=use_case, error_type=error_type)


def emit_model_loaded(model_name: str) -> None:
    emit_counter("ml.startup.model_loaded", 1, model_name=model_name)
