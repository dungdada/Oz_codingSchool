from pathlib import Path

import pytest

from app.ml import pneumonia_predictor

torch = pytest.importorskip("torch")


class FakeModel:
    def __call__(self, _tensor):
        return torch.tensor([[0.1, 2.0]])


def test_predicts_pneumonia_from_second_class(monkeypatch):
    monkeypatch.setattr(
        pneumonia_predictor,
        "_prepare_image",
        lambda _path: torch.zeros((1, 3, 224, 224)),
    )
    monkeypatch.setattr(pneumonia_predictor, "_load_model", lambda: FakeModel())

    prediction = pneumonia_predictor.predict_pneumonia(Path("unused.jpg"))

    assert prediction.is_pneumonia is True
    assert prediction.confidence > 50
