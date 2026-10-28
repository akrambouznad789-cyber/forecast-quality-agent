# Forecast-Quality Analysis Agent: an LLM Agent for Supply Chain Planners

[![tests](https://github.com/akrambouznad789-cyber/forecast-quality-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/akrambouznad789-cyber/forecast-quality-agent/actions/workflows/tests.yml)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Planners spend hours checking which forecasts went wrong, by how much, and whether the prediction intervals held.
Supply chain planning software now ships AI agents for this kind of work, but an agent is only useful if its numbers
are right. This project measures how often an LLM agent that calls forecasting tools reports the right numbers,
compared with the same LLM without tools.

> **Status: work in progress** (started October 2026). Done: the agent's tools and a reproducible reference
> question set, both covered by unit tests. Next: the agent loop with tool calling and the control conditions.
> See the [roadmap](#roadmap).

## Research question
Can an LLM agent that calls forecasting tools answer planners' questions about forecast quality more accurately
than the same LLM without tools?

## Hypotheses
- **H1.** With tools, the agent's numeric answers match the reference far more often than the LLM alone.
- **H2.** With tools, the rate of hallucinated numbers (numbers found in no tool output) drops close to zero.
- **H3.** The remaining errors are mostly tool-selection or argument errors (wrong series, wrong date), which an
  error analysis can classify.

## Design

### Tools
Each tool returns plain JSON-serializable data, so the model reads the numbers instead of guessing them
([`planning_tools.py`](planning_tools.py)).

| Tool | Arguments | Returns |
|---|---|---|
| `get_forecast` | `series_id`, `date` | Point forecast, 80% prediction interval, actual demand, whether the actual fell inside |
| `forecast_quality_summary` | `series_id` | MASE, 80% interval coverage, mean bias in units per day, over- or under-forecast |
| `rank_series_by_forecast_error` | `top_n` | The store-departments with the highest MASE |

Unknown series and dates outside the test window raise an error instead of returning a guess, so the agent sees
its own argument errors.

```python
>>> from planning_tools import get_forecast, forecast_quality_summary
>>> get_forecast("CA_3_FOODS_2", "2016-05-05")
{'series_id': 'CA_3_FOODS_2', 'date': '2016-05-05', 'point_forecast': 529.0, 'interval_80': [340.9, 720.4], 'actual': 738.0, 'actual_inside_interval': False}
>>> forecast_quality_summary("WI_2_FOODS_1")
{'series_id': 'WI_2_FOODS_1', 'mase': 2.091, 'coverage_80': 0.393, 'mean_bias_units_per_day': -124.9, 'direction': 'under-forecast'}
```

### Evaluation set
[`evaluation/questions.jsonl`](evaluation/questions.jsonl) holds 21 planner questions with reference answers:
10 interval lookups, 10 bias diagnoses and 1 ranking question. Series and dates are sampled with a fixed seed (2026),
and the reference answers are exact lookups computed by the tools. A unit test rebuilds the set from the seed and
checks that it matches the committed file.

```json
{"question_id": "interval_lookup_01", "type": "interval_lookup", "question": "What was the 80% prediction interval for CA_3_FOODS_2 on 2016-05-05, and did actual demand fall inside it?", "reference_answer": {"series_id": "CA_3_FOODS_2", "date": "2016-05-05", "point_forecast": 529.0, "interval_80": [340.9, 720.4], "actual": 738.0, "actual_inside_interval": false}}
```

### Protocol (next)
- **Conditions.** The same LLM answers every question three times:
  1. **with tools**: it can call the three tools above;
  2. **data in context**: no tools, but the same forecast table is pasted into the prompt, so both conditions
     have the same information;
  3. **no data**: measures whether the model admits it cannot answer or invents numbers.
- **Metrics.** The share of answers within tolerance of the reference; the hallucinated-number rate; and tool-call
  accuracy (right tool, right arguments).
- **Pre-registration.** The tolerance and scoring rules will be committed to this README before the first agent run,
  so they cannot be tuned to the results.
- **Error analysis.** Every wrong answer is classified as a wrong tool, wrong arguments, a misread tool output or an
  unsupported number.

### Data
[`data/`](data) holds the forecasts and scores of the companion project
[demand-forecasting-benchmark](https://github.com/akrambouznad789-cyber/demand-forecasting-benchmark): M5 Walmart
sales, 70 store × department series, 28-day test window (2016-04-25 to 2016-05-22), seasonal naive baseline with
empirical 80% intervals. The files were copied from that project's `results/` folder at commit
[`be56a45`](https://github.com/akrambouznad789-cyber/demand-forecasting-benchmark/tree/be56a4581ee0bf29c67ee0b8fc2ae1ece8d65a7a/results).
When the benchmark adds models, the files will be refreshed and the new commit recorded here.

## Reproducing
Requires Python 3.12 or later.

```bash
git clone https://github.com/akrambouznad789-cyber/forecast-quality-agent.git
cd forecast-quality-agent
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python build_evaluation_questions.py   # rebuilds evaluation/questions.jsonl (identical for seed 2026)
```

### Tests
```bash
pip install -r requirements-dev.txt
pytest
```
The tests check that every tool output is consistent with the data, that bad arguments fail loudly, and that the
evaluation set is reproducible. The agent will be scored against these tools, so a wrong tool would silently
corrupt the evaluation. GitHub Actions runs the tests on every push.

## Repository structure
```
├── planning_tools.py              # the tools the agent can call
├── build_evaluation_questions.py  # builds the reference question set
├── evaluation/questions.jsonl     # 21 questions with reference answers
├── data/                          # forecasts and scores from demand-forecasting-benchmark
└── tests/                         # unit tests (pytest)
```

## Roadmap
- [x] Tools over the forecasts and scores, with unit tests
- [x] Reproducible evaluation set with reference answers (21 questions)
- [ ] Agent loop with tool calling; data-in-context and no-data controls
- [ ] Pre-registered scoring rules, scoring script and error analysis
- [ ] Larger question set, including questions that need several tool calls

## References
- Hyndman, R. J., & Koehler, A. B. (2006). Another look at measures of forecast accuracy. *International Journal of
  Forecasting*, 22(4), 679–688. https://doi.org/10.1016/j.ijforecast.2006.03.001
- Schick, T., et al. (2023). Toolformer: Language models can teach themselves to use tools. *NeurIPS 2023*.
  [arXiv:2302.04761](https://arxiv.org/abs/2302.04761)
- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning
  and acting in language models. *ICLR 2023*. [arXiv:2210.03629](https://arxiv.org/abs/2210.03629)

## Citation
If this project is useful in your work, please cite it using [CITATION.cff](CITATION.cff) (GitHub's
"Cite this repository" button).

## License
The code is released under the [MIT License](LICENSE). The forecasts in `data/` are derived from the M5 competition
data, which belong to their providers.

## Author
Akram Bouznad, research master's student (M.A.Sc.) in industrial engineering, data science profile, Polytechnique
Montréal · [LinkedIn](https://www.linkedin.com/in/akram-bouznad-68aa7b292/)
