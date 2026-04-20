import json

from superset.app import create_app


def _canonical_operator(operator: str | None) -> str | None:
    mapping = {
        "GREATER_THAN": ">",
        ">": ">",
        "LESS_THAN": "<",
        "<": "<",
        "EQUALS": "==",
        "==": "==",
        "NOT_EQUALS": "!=",
        "!=": "!=",
        "IN": "IN",
        "NOT_IN": "NOT IN",
        "IS_NULL": "IS NULL",
        "IS_NOT_NULL": "IS NOT NULL",
        "TEMPORAL_RANGE": "TEMPORAL_RANGE",
    }
    return mapping.get(operator or "", operator)


def _build_filters(form_data: dict) -> list[dict]:
    filters: list[dict] = []
    for adhoc_filter in form_data.get("adhoc_filters") or []:
        if adhoc_filter.get("expressionType") != "SIMPLE":
            continue
        subject = adhoc_filter.get("subject")
        if not subject:
            continue
        filters.append(
            {
                "col": subject,
                "op": _canonical_operator(
                    adhoc_filter.get("operatorId") or adhoc_filter.get("operator")
                ),
                "val": adhoc_filter.get("comparator"),
            }
        )
    return filters


def _canonical_form_data(slice_) -> dict | None:
    form_data = slice_.params_dict or {}
    x_axis = form_data.get("x_axis") or (form_data.get("groupby") or [None])[0]
    metrics = form_data.get("metrics") or ([form_data["metric"]] if form_data.get("metric") else [])
    if not x_axis or not metrics:
        return None

    return {
        "adhoc_filters": form_data.get("adhoc_filters") or [],
        "annotation_layers": form_data.get("annotation_layers") or [],
        "color_scheme": form_data.get("color_scheme", "supersetColors"),
        "comparison_type": form_data.get("comparison_type", "values"),
        "contributionMode": form_data.get("contributionMode"),
        "datasource": f"{slice_.datasource.id}__table",
        "groupby": [],
        "markerEnabled": bool(form_data.get("markerEnabled", False)),
        "metrics": metrics,
        "orientation": form_data.get("orientation", "vertical"),
        "order_bars": bool(form_data.get("order_bars", False)),
        "queryFields": {"columns": "groupby", "groupby": "groupby", "metrics": "metrics"},
        "row_limit": form_data.get("row_limit", 10000),
        "show_extra_controls": False,
        "show_legend": bool(form_data.get("show_legend", False)),
        "show_value": bool(form_data.get("show_value", form_data.get("show_bar_value", False))),
        "slice_id": slice_.id,
        "stack": form_data.get("stack"),
        "truncateXAxis": bool(form_data.get("truncateXAxis", True)),
        "truncateYAxis": bool(form_data.get("truncateYAxis", True)),
        "viz_type": "echarts_timeseries_bar",
        "xAxisLabelRotation": int(form_data.get("xAxisLabelRotation", 0)),
        "x_axis": x_axis,
        "x_axis_title": form_data.get("x_axis_title", form_data.get("x_axis_label", x_axis)),
        "x_axis_title_margin": int(form_data.get("x_axis_title_margin", 30)),
        "y_axis_title": form_data.get("y_axis_title", ""),
        "y_axis_title_margin": int(form_data.get("y_axis_title_margin", 0)),
        "y_axis_format": form_data.get("y_axis_format", "SMART_NUMBER"),
        "zoomable": bool(form_data.get("zoomable", False)),
    }


def _query_context_dict(slice_, form_data: dict) -> dict:
    x_axis = form_data["x_axis"]
    metrics = form_data["metrics"]
    return {
        "datasource": {"id": slice_.datasource.id, "type": slice_.datasource.type},
        "force": False,
        "queries": [
            {
                "filters": _build_filters(form_data),
                "extras": {"having": "", "where": ""},
                "applied_time_extras": {},
                "columns": [
                    {
                        "columnType": "BASE_AXIS",
                        "sqlExpression": x_axis,
                        "label": x_axis,
                        "expressionType": "SQL",
                    }
                ],
                "metrics": metrics,
                "orderby": [[metrics[0], False]] if form_data["order_bars"] else [],
                "annotation_layers": [],
                "row_limit": form_data["row_limit"],
                "series_columns": [],
                "series_limit": 0,
                "order_desc": form_data["order_bars"],
                "url_params": {},
                "custom_params": {},
                "custom_form_data": {},
                "time_offsets": [],
                "post_processing": [
                    {
                        "operation": "pivot",
                        "options": {
                            "index": [x_axis],
                            "columns": [],
                            "aggregates": {metric: {"operator": "mean"} for metric in metrics},
                            "drop_missing_columns": True,
                        },
                    },
                    {"operation": "flatten"},
                ],
            }
        ],
        "form_data": {
            **form_data,
            "force": False,
            "result_format": "json",
            "result_type": "full",
        },
        "result_format": "json",
        "result_type": "full",
    }


def normalize_bar_chart_query_contexts() -> int:
    app = create_app()
    with app.app_context():
        from flask import g
        from superset import security_manager
        from superset.extensions import db
        from superset.models.slice import Slice

        g.user = security_manager.find_user(username="admin")
        slices = db.session.query(Slice).filter(Slice.viz_type == "echarts_timeseries_bar")
        normalized = 0
        for slice_ in slices:
            form_data = _canonical_form_data(slice_)
            if form_data is None:
                continue
            slice_.params = json.dumps(form_data, ensure_ascii=False)
            slice_.query_context = json.dumps(
                _query_context_dict(slice_, form_data), ensure_ascii=False
            )
            normalized += 1
        db.session.commit()
        return normalized


if __name__ == "__main__":
    normalized = normalize_bar_chart_query_contexts()
    print(f"Normalized {normalized} echarts_timeseries_bar charts.")
