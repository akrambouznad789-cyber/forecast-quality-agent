"""Tools the forecast-quality agent can call.

Each tool returns plain JSON-serializable data, so the LLM reads the numbers instead of guessing them.
The forecasts and scores come from the demand-forecasting-benchmark project (copied into data/).
"""
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIRECTORY = Path(__file__).resolve().parent / "data"
FORECASTS_CSV = DATA_DIRECTORY / "forecasts_seasonal_naive.csv"
SCORES_CSV = DATA_DIRECTORY / "scores_seasonal_naive.csv"


@lru_cache(maxsize=1)
def load_forecasts() -> pd.DataFrame:
    return pd.read_csv(FORECASTS_CSV)


@lru_cache(maxsize=1)
def load_scores() -> pd.DataFrame:
    return pd.read_csv(SCORES_CSV)


def get_forecast(series_id: str, date: str) -> dict:
    """Forecast, 80% prediction interval and actual demand for one store-department on one day."""
    forecasts = load_forecasts()
    matching_rows = forecasts[(forecasts["series_id"] == series_id) & (forecasts["date"] == date)]
    if matching_rows.empty:
        raise ValueError(f"No forecast for series '{series_id}' on {date}")
    row = matching_rows.iloc[0]
    return {
        "series_id": series_id,
        "date": date,
        "point_forecast": round(float(row["point_forecast"]), 1),
        "interval_80": [round(float(row["quantile_0.1"]), 1), round(float(row["quantile_0.9"]), 1)],
        "actual": float(row["actual"]),
        "actual_inside_interval": bool(row["quantile_0.1"] <= row["actual"] <= row["quantile_0.9"]),
    }


def forecast_quality_summary(series_id: str) -> dict:
    """Accuracy, calibration and bias of the forecast for one store-department over the test window.
    A positive bias means the forecast was too high on average (over-forecasting)."""
    scores = load_scores()
    score_rows = scores[scores["series_id"] == series_id]
    if score_rows.empty:
        raise ValueError(f"No scores for series '{series_id}'")
    forecasts = load_forecasts()
    series_forecasts = forecasts[forecasts["series_id"] == series_id]
    mean_bias_units_per_day = float((series_forecasts["point_forecast"] - series_forecasts["actual"]).mean())
    return {
        "series_id": series_id,
        "mase": round(float(score_rows.iloc[0]["mase"]), 3),
        "coverage_80": round(float(score_rows.iloc[0]["coverage_80"]), 3),
        "mean_bias_units_per_day": round(mean_bias_units_per_day, 1),
        "direction": "over-forecast" if mean_bias_units_per_day > 0 else "under-forecast",
    }


def rank_series_by_forecast_error(top_n: int = 5) -> list[dict]:
    """The store-departments with the worst MASE (least accurate forecasts) first."""
    worst_series = load_scores().sort_values("mase", ascending=False).head(top_n)
    return [{"series_id": row["series_id"], "mase": round(float(row["mase"]), 3)} for _, row in worst_series.iterrows()]
