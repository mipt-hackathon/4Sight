from dataclasses import dataclass, field
from datetime import date


@dataclass
class ChurnResult:
    probability: float
    top_factors: list[dict[str, str]] | None = None


@dataclass
class RecommendationItem:
    item_id: str
    score: float | None = None
    reason: str | None = None


@dataclass
class RecommendationResult:
    items: list[RecommendationItem] = field(default_factory=list)


@dataclass
class ForecastPoint:
    date: date
    value: float


@dataclass
class ForecastResult:
    forecast: list[ForecastPoint] = field(default_factory=list)


@dataclass
class SegmentationResult:
    segment: str
    rfm_code: str | None = None
    cluster_id: int | None = None
