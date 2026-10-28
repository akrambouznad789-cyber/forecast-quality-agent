"""Build the evaluation set: planner questions with their reference answers.

The reference answers come from the tools themselves, which are plain lookups over the data. The evaluation
then measures whether an LLM reports those numbers faithfully, with and without access to the tools.

Usage: python build_evaluation_questions.py
"""
import json
import random
from pathlib import Path

from planning_tools import forecast_quality_summary, get_forecast, load_forecasts, rank_series_by_forecast_error

QUESTIONS_PER_TYPE = 10
RANDOM_SEED = 2026
OUTPUT_FILE = Path(__file__).resolve().parent / "evaluation" / "questions.jsonl"


def build_questions(random_seed: int = RANDOM_SEED) -> list[dict]:
    """The same seed always gives the same questions, so the evaluation set can be rebuilt and checked."""
    random_generator = random.Random(random_seed)
    forecasts = load_forecasts()
    all_series_ids = sorted(forecasts["series_id"].unique())
    all_dates = sorted(forecasts["date"].unique())
    questions = []

    for question_number in range(1, QUESTIONS_PER_TYPE + 1):
        series_id, date = random_generator.choice(all_series_ids), random_generator.choice(all_dates)
        questions.append({
            "question_id": f"interval_lookup_{question_number:02d}",
            "type": "interval_lookup",
            "question": f"What was the 80% prediction interval for {series_id} on {date}, and did actual demand fall inside it?",
            "reference_answer": get_forecast(series_id, date),
        })

    for question_number, series_id in enumerate(random_generator.sample(all_series_ids, QUESTIONS_PER_TYPE), start=1):
        questions.append({
            "question_id": f"bias_diagnosis_{question_number:02d}",
            "type": "bias_diagnosis",
            "question": f"Over the last four weeks, did we over-forecast or under-forecast {series_id}, and by how many units per day on average?",
            "reference_answer": forecast_quality_summary(series_id),
        })

    questions.append({
        "question_id": "ranking_01",
        "type": "ranking",
        "question": "Which five store-departments had the least accurate forecasts over the last four weeks?",
        "reference_answer": rank_series_by_forecast_error(top_n=5),
    })
    return questions


def main():
    questions = build_questions()
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as output:
        for question in questions:
            output.write(json.dumps(question) + "\n")
    print(f"{len(questions)} questions written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
