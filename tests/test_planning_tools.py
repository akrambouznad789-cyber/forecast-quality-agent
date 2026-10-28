"""Check that the tools return numbers consistent with the data, and fail loudly on bad arguments.

The agent's answers will be scored against these tools, so a wrong tool would silently corrupt the evaluation.
"""
import pandas as pd
import pytest

from planning_tools import (FORECASTS_CSV, SCORES_CSV, forecast_quality_summary, get_forecast, load_forecasts,
                            rank_series_by_forecast_error)


def test_actual_inside_interval_matches_the_interval_on_every_row():
    for _, row in load_forecasts().iterrows():
        answer = get_forecast(row["series_id"], row["date"])
        lower_bound, upper_bound = answer["interval_80"]
        assert answer["actual_inside_interval"] == (row["quantile_0.1"] <= row["actual"] <= row["quantile_0.9"])
        assert lower_bound <= upper_bound


def test_get_forecast_rejects_an_unknown_series_or_a_date_outside_the_test_window():
    with pytest.raises(ValueError):
        get_forecast("XX_9_FOODS_1", "2016-05-01")
    with pytest.raises(ValueError):
        get_forecast("CA_1_FOODS_1", "2016-06-30")


def test_bias_direction_follows_the_sign_of_the_mean_error():
    forecasts = pd.read_csv(FORECASTS_CSV)
    for series_id in forecasts["series_id"].unique():
        summary = forecast_quality_summary(series_id)
        series_forecasts = forecasts[forecasts["series_id"] == series_id]
        mean_error = (series_forecasts["point_forecast"] - series_forecasts["actual"]).mean()
        # The tool rounds to one decimal, so it can differ from the exact mean by up to half a tenth.
        assert summary["mean_bias_units_per_day"] == pytest.approx(mean_error, abs=0.05 + 1e-9)
        assert summary["direction"] == ("over-forecast" if mean_error > 0 else "under-forecast")


def test_forecast_quality_summary_rejects_an_unknown_series():
    with pytest.raises(ValueError):
        forecast_quality_summary("XX_9_FOODS_1")


def test_ranking_lists_the_highest_mase_first():
    ranking = rank_series_by_forecast_error(top_n=5)
    highest_mase_series = pd.read_csv(SCORES_CSV).sort_values("mase", ascending=False)["series_id"].head(5).tolist()
    assert [entry["series_id"] for entry in ranking] == highest_mase_series
    assert [entry["mase"] for entry in ranking] == sorted((entry["mase"] for entry in ranking), reverse=True)
