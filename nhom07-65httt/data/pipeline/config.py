from pathlib import Path

import yaml


def load_settings(path: str | Path = "data/config.yaml") -> tuple[dict, Path]:
    source = Path(path).resolve()
    values = yaml.safe_load(source.read_text(encoding="utf-8")) if source.exists() else {}
    if not isinstance(values, dict):
        raise ValueError(f"Tệp cấu hình phải có dạng mapping YAML: {source}")
    project_root = source.parent.parent
    return values, project_root


def resolve_path(project_root: Path, value: str | None, default: str | None = None) -> Path | None:
    raw = value or default
    if raw is None:
        return None
    path = Path(raw)
    return path if path.is_absolute() else project_root / path
