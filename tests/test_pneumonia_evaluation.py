import pytest

from app.ml.pneumonia_evaluation import evaluate_predictions


def test_model_meets_recall_and_accuracy_requirements():
    metrics = evaluate_predictions(
        actual=[True] * 10 + [False] * 10,
        predicted=[True] * 9 + [False] + [True] * 2 + [False] * 8,
    )

    assert metrics.recall == pytest.approx(0.9)
    assert metrics.accuracy == pytest.approx(0.85)
    assert metrics.meets_acceptance_criteria is True


def test_model_fails_when_recall_is_below_minimum():
    metrics = evaluate_predictions(
        actual=[True] * 10 + [False] * 10,
        predicted=[True] * 8 + [False] * 2 + [False] * 10,
    )

    assert metrics.recall == pytest.approx(0.8)
    assert metrics.meets_acceptance_criteria is False


def test_evaluation_requires_positive_sample():
    with pytest.raises(ValueError, match="양성 표본"):
        evaluate_predictions([False, False], [False, False])
