from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from app.services.medical_record_service import MedicalRecordService


class FakeRepository:
    def __init__(self, patient: object | None = object()) -> None:
        self.patient = patient
        self.created: dict | None = None

    async def get_active_patient(self, patient_id: int) -> object | None:
        return self.patient

    async def create(self, **kwargs):
        self.created = kwargs
        return kwargs


@pytest.mark.asyncio
async def test_rejects_unsupported_image_before_lookup(tmp_path):
    repository = FakeRepository()
    service = MedicalRecordService(repository, tmp_path)
    upload = UploadFile(filename="xray.gif", file=BytesIO(b"GIF89a"))

    with pytest.raises(HTTPException) as error:
        await service.create_medical_record(
            patient_id=15,
            chart_number="CH-1",
            symptom="기침",
            xray_image=upload,
        )

    assert error.value.status_code == 415
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_returns_404_when_patient_does_not_exist(tmp_path):
    service = MedicalRecordService(FakeRepository(patient=None), tmp_path)
    upload = UploadFile(filename="xray.png", file=BytesIO(b"png"))

    with pytest.raises(HTTPException) as error:
        await service.create_medical_record(
            patient_id=999,
            chart_number="CH-1",
            symptom="기침",
            xray_image=upload,
        )

    assert error.value.status_code == 404
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_saves_image_and_creates_record(tmp_path):
    repository = FakeRepository()
    service = MedicalRecordService(repository, tmp_path)
    upload = UploadFile(filename="chest_xray.JPEG", file=BytesIO(b"image-data"))

    await service.create_medical_record(
        patient_id=15,
        chart_number="CH-20260720-001",
        symptom="지속적인 기침과 발열 증상",
        xray_image=upload,
    )

    saved_files = list(tmp_path.iterdir())
    assert len(saved_files) == 1
    assert saved_files[0].suffix == ".jpeg"
    assert saved_files[0].read_bytes() == b"image-data"
    assert repository.created is not None
    assert repository.created["xray_image_url"].startswith("/uploads/xray/")
