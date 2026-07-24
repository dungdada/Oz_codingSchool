from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.models.medical_record import MedicalRecord
from app.repositories.medical_record_repository import MedicalRecordRepository

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
UPLOAD_CHUNK_SIZE = 1024 * 1024


class MedicalRecordService:
    def __init__(
        self,
        repository: MedicalRecordRepository,
        upload_dir: Path,
    ) -> None:
        self.repository = repository
        self.upload_dir = upload_dir

    async def create_medical_record(
        self,
        *,
        patient_id: int,
        chart_number: str,
        symptom: str,
        xray_image: UploadFile,
    ) -> MedicalRecord:
        extension = Path(xray_image.filename or "").suffix.lower()
        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="지원하지 않는 이미지 형식입니다.",
            )

        patient = await self.repository.get_active_patient(patient_id)
        if patient is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 환자입니다.",
            )

        self.upload_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid4().hex}{extension}"
        stored_path = self.upload_dir / stored_name
        image_url = f"/uploads/xray/{stored_name}"

        try:
            with stored_path.open("wb") as destination:
                while chunk := await xray_image.read(UPLOAD_CHUNK_SIZE):
                    destination.write(chunk)

            return await self.repository.create(
                patient_id=patient_id,
                chart_number=chart_number,
                symptom=symptom,
                xray_image_url=image_url,
            )
        except Exception:
            stored_path.unlink(missing_ok=True)
            raise
        finally:
            await xray_image.close()
