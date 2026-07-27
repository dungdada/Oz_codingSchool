from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PneumoniaModelMetrics:
    true_positive: int
    false_positive: int
    false_negative: int
    true_negative: int
    recall: float
    accuracy: float

    @property
    def meets_acceptance_criteria(self) -> bool:
        return self.recall >= 0.90 and self.accuracy >= 0.80


def evaluate_predictions(
    actual: Iterable[bool],
    predicted: Iterable[bool],
) -> PneumoniaModelMetrics:
    actual_values = list(actual)
    predicted_values = list(predicted)
    if len(actual_values) != len(predicted_values):
        raise ValueError("실제값과 예측값의 개수가 같아야 합니다.")
    if not actual_values:
        raise ValueError("평가 표본이 하나 이상 필요합니다.")

    tp = sum(a and p for a, p in zip(actual_values, predicted_values))
    fp = sum(not a and p for a, p in zip(actual_values, predicted_values))
    fn = sum(a and not p for a, p in zip(actual_values, predicted_values))
    tn = sum(not a and not p for a, p in zip(actual_values, predicted_values))
    positive_count = tp + fn
    if positive_count == 0:
        raise ValueError("Recall 평가를 위해 폐렴 양성 표본이 필요합니다.")

    return PneumoniaModelMetrics(
        true_positive=tp,
        false_positive=fp,
        false_negative=fn,
        true_negative=tn,
        recall=tp / positive_count,
        accuracy=(tp + tn) / len(actual_values),
    )
