from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.config import settings


@dataclass(frozen=True)
class PneumoniaPrediction:
    is_pneumonia: bool
    confidence: float


def _model_path() -> Path:
    path = Path(settings.AI_MODEL_PATH)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    if not path.is_file():
        raise RuntimeError(f"AI 모델 파일을 찾을 수 없습니다: {path}")
    return path


@lru_cache(maxsize=1)
def load_model():
    import torch
    import timm

    model = timm.create_model(
        settings.AI_MODEL_ARCHITECTURE,
        pretrained=False,
        num_classes=settings.AI_MODEL_NUM_CLASSES,
    )
    state_dict = torch.load(
        _model_path(),
        map_location="cpu",
        weights_only=True,
    )
    model.load_state_dict(state_dict, strict=True)
    model.eval()
    return model


def _prepare_image(image_path: Path):
    import numpy as np
    import torch
    from PIL import Image

    imagenet_mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    imagenet_std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    with Image.open(image_path) as image:
        image = image.convert("RGB").resize(
            (settings.AI_IMAGE_SIZE, settings.AI_IMAGE_SIZE)
        )
        array = np.asarray(image, dtype=np.float32) / 255.0
    array = (array - imagenet_mean) / imagenet_std
    return torch.from_numpy(array.transpose(2, 0, 1)).unsqueeze(0)


def predict_pneumonia(image_path: Path) -> PneumoniaPrediction:
    import torch

    tensor = _prepare_image(image_path)
    with torch.inference_mode():
        output = load_model()(tensor)

    if not isinstance(output, torch.Tensor):
        raise RuntimeError("AI 모델 출력 형식이 올바르지 않습니다.")
    logits = output.squeeze()
    if logits.numel() == 1:
        pneumonia_probability = torch.sigmoid(logits).item()
    elif logits.numel() == 2:
        pneumonia_probability = torch.softmax(logits, dim=0)[
            settings.AI_PNEUMONIA_CLASS_INDEX
        ].item()
    else:
        raise RuntimeError(f"지원하지 않는 클래스 수입니다: {logits.numel()}")

    is_pneumonia = pneumonia_probability >= settings.AI_DECISION_THRESHOLD
    confidence = (
        pneumonia_probability if is_pneumonia else 1.0 - pneumonia_probability
    )
    return PneumoniaPrediction(
        is_pneumonia=is_pneumonia,
        confidence=round(confidence * 100, 2),
    )
