import yaml
from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.schemas.common import ErrorOut, PlatformOut

router = APIRouter(prefix="/api/v1", tags=["Nền tảng"])


def load_platforms() -> list[PlatformOut]:
    path = get_settings().resolve_platforms_file()
    if path is None:
        raise HTTPException(status_code=503, detail="Không tìm thấy config/platforms.yml")
    try:
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise HTTPException(status_code=503, detail=f"Không đọc được platforms.yml ({type(exc).__name__})") from exc

    items = config.get("platforms") if isinstance(config, dict) else None
    if not isinstance(items, list):
        raise HTTPException(status_code=503, detail='platforms.yml thiếu danh sách "platforms"')

    result: list[PlatformOut] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        result.append(
            PlatformOut(
                id=str(item["id"]),
                group=str(item.get("platform_group", "")),
                play_id=str(item["play_id"]) if item.get("play_id") else None,
                ios_id=str(item["ios_id"]) if item.get("ios_id") else None,
            )
        )
    return result


@router.get(
    "/platforms",
    response_model=list[PlatformOut],
    responses={503: {"model": ErrorOut}},
    summary="Danh sách nền tảng từ config/platforms.yml",
)
def list_platforms() -> list[PlatformOut]:
    return load_platforms()
