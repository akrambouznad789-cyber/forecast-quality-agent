# Forecast-Quality Analysis Agent: an LLM Agent for Supply Chain Planners

**Status: in progress** (started 2026-10-27) · Akram Bouznad, Polytechnique Montréal

## Research question
Can an LLM agent that calls forecasting tools answer planners' questions about forecast quality more accurately
than the same LLM without tools?

Planners spend hours checking which forecasts went wrong, by how much, and whether the prediction intervals held.
Supply chain planning software now ships AI agents for this kind of work. An agent is only useful if its numbers
are right, so this project measures that.

## Hypotheses
- **H1.** With tools, the agent's numeric answers match the reference far more often than the LLM alone.
- **H2.** With tools, the rate of hallucinated numbers (numbers found in no tool output) drops close to zero.
- **H3.** The remaining errors are mostly tool-selection or argument errors (wrong series, wrong date), which an
  error analysis can classify.

## Design
- **Tools** (`planning_tools.py`, done): `get_forecast` (forecast, 80% interval, actual demand),
  `forecast_quality_summary` (MASE, interval coverage, bias), `rank_series_by_forecast_error`.
- **Data:** the forecasts and scores of the companion project
  [demand-forecasting-benchmark](https://github.com/akrambouznad789-cyber/demand-forecasting-benchmark) (M5 Walmart data, store × department level,
  seasonal naive baseline for now; foundation models next).
- **Evaluation set** (`build_evaluation_questions.py`, done): 21 planner questions with reference answers
  (interval lookups, bias diagnosis, ranking of the worst forecasts).
- **Agent loop** (next): the same LLM answers every question twice, with and without tool calling.
- **Metrics:** share of answers within tolerance of the reference, hallucinated-number rate, tool-call accuracy.

## Roadmap
- [x] Tools over the forecasts and scores
- [x] Evaluation set with reference answers (21 questions)
- [ ] Agent loop with tool calling; LLM-only control
- [ ] Scoring script and error analysis
- [ ] Larger question set, including questions that need several tool calls

## Run
```
pip install -r requirements.txt
python build_evaluation_questions.py
```
