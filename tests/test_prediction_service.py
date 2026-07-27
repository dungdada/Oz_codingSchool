import time
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.ml.pneumonia_predictor import PneumoniaPrediction
from app.services.prediction_service import PredictionService


class FakeDB:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def refresh(self, _value) -> None:
        return None


class FakeRepository:
    def __init__(
        self,
        *,
        record=None,
        cached=None,
        analyses=None,
    ) -> None:
        self.db = FakeDB()
        self.record = record
        self.cached = cached
        self.analyses = analyses or []
        self.created = None

    async def get_medical_record(self, _record_id):
        return self.record

    async def get_by_record_and_model(self, **_kwargs):
        return self.cached

    async def list_by_record(self, _record_id):
        return self.analyses

    async def create(self, **kwargs):
        self.created = kwargs
        return SimpleNamespace(
            id=1,
            medical_record_id=kwargs["record_id"],
            created_by=kwargs["created_by"],
            is_pneumonia=kwargs["is_pneumonia"],
            confidence=kwargs["confidence"],
            ai_model=kwargs["ai_model"],
            heatmap_image_url=kwargs["heatmap_image_url"],
            created_at=None,
        )


@pytest.mark.anyio
async def test_returns_cached_prediction_without_running_model(tmp_path):
    cached = SimpleNamespace(id=7)
    repository = FakeRepository(
        record=SimpleNamespace(xray_image_url="/uploads/xray/a.png"),
        cached=cached,
    )

    def predictor(_path):
        raise AssertionError("캐시가 있으면 모델을 실행하면 안 됩니다.")

    service = PredictionService(repository, tmp_path, predictor)
    result = await service.predict(record_id=3, user_id=9)

    assert result.analysis is cached
    assert result.cached is True
    assert repository.db.commits == 0


@pytest.mark.anyio
async def test_runs_model_once_and_stores_prediction(tmp_path):
    image_path = tmp_path / "a.png"
    image_path.write_bytes(b"xray")
    repository = FakeRepository(
        record=SimpleNamespace(
            xray_image_url="/uploads/xray/a.png"
        )
    )
    calls = 0

    def predictor(_path):
        nonlocal calls
        calls += 1
        return PneumoniaPrediction(
            is_pneumonia=True,
            confidence=94.25,
        )

    service = PredictionService(repository, tmp_path, predictor)
    result = await service.predict(record_id=3, user_id=9)

    assert calls == 1
    assert result.cached is False
    assert repository.created is not None
    assert repository.created["confidence"] == Decimal("94.25")
    assert repository.created["heatmap_image_url"] is None
    assert repository.db.commits == 1


@pytest.mark.anyio
async def test_returns_404_when_medical_record_does_not_exist(
    tmp_path,
):
    service = PredictionService(
        FakeRepository(record=None),
        tmp_path,
        lambda _path: None,
    )

    with pytest.raises(HTTPException) as error:
        await service.predict(record_id=999, user_id=9)

    assert error.value.status_code == 404


@pytest.mark.anyio
async def test_times_out_slow_inference(tmp_path, monkeypatch):
    image_path = tmp_path / "a.png"
    image_path.write_bytes(b"xray")
    repository = FakeRepository(
        record=SimpleNamespace(
            xray_image_url="/uploads/xray/a.png"
        )
    )

    def slow_predictor(_path):
        time.sleep(0.05)
        return PneumoniaPrediction(
            is_pneumonia=False,
            confidence=80.0,
        )

    monkeypatch.setattr(
        "app.services.prediction_service."
        "settings.AI_INFERENCE_TIMEOUT_SECONDS",
        0.001,
    )
    service = PredictionService(
        repository,
        tmp_path,
        slow_predictor,
    )

    with pytest.raises(HTTPException) as error:
        await service.predict(record_id=3, user_id=9)

    assert error.value.status_code == 504
