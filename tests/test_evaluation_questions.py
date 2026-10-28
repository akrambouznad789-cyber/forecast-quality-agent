"""Check that the committed evaluation set is exactly what the builder produces, and is well formed."""
import json

from build_evaluation_questions import OUTPUT_FILE, QUESTIONS_PER_TYPE, build_questions


def load_committed_questions() -> list[dict]:
    with OUTPUT_FILE.open(encoding="utf-8") as questions_file:
        return [json.loads(line) for line in questions_file]


def test_committed_evaluation_set_is_reproducible_from_the_seed():
    assert build_questions() == load_committed_questions()


def test_question_ids_are_unique_and_types_are_balanced():
    questions = load_committed_questions()
    question_ids = [question["question_id"] for question in questions]
    assert len(question_ids) == len(set(question_ids))
    for question_type in ["interval_lookup", "bias_diagnosis"]:
        assert sum(question["type"] == question_type for question in questions) == QUESTIONS_PER_TYPE


def test_every_question_has_a_reference_answer():
    for question in load_committed_questions():
        assert question["question"].strip()
        assert question["reference_answer"]
