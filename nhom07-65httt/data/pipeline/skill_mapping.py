from pathlib import Path

import yaml

from .cleaner import normalize_key


def load_taxonomy(path: str | Path | None):
    if not path:
        return None
    source = Path(path)
    if not source.exists():
        return None
    values = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    skills = values.get("skills", []) if isinstance(values, dict) else []
    if not isinstance(skills, list):
        raise ValueError("Trường taxonomy 'skills' phải là một danh sách")
    normalized = []
    for entry in skills:
        if not isinstance(entry, dict) or not entry.get("name"):
            continue
        normalized.append({
            "name": str(entry["name"]).strip(),
            "aliases": [str(x).strip() for x in entry.get("aliases", []) if str(x).strip()],
            "keywords": [str(x).strip() for x in entry.get("keywords", []) if str(x).strip()],
        })
    return normalized


def map_skills(record: dict, taxonomy: list[dict] | None) -> dict:
    source = record.get("source_metadata") or {}
    direct_source = source.get("direct_skills") or source.get("skills")
    if isinstance(direct_source, list):
        direct = [str(x).strip() for x in direct_source if str(x).strip()]
    elif direct_source:
        direct = [x.strip() for x in str(direct_source).replace(";", ",").split(",") if x.strip()]
    else:
        direct = []
    if not taxonomy:
        record["direct_skills"] = direct or None
        record["inferred_skills"] = None
        record["skills"] = direct or None
        return record

    alias_map = {}
    for item in taxonomy:
        for name in [item["name"], *item["aliases"]]:
            alias_map[normalize_key(name)] = item["name"]
    mapped_direct = list(dict.fromkeys(alias_map.get(normalize_key(skill), skill) for skill in direct))
    evidence = " ".join(filter(None, [record.get("title"), record.get("clean_description")])).casefold()
    inferred = []
    for item in taxonomy:
        if item["name"] in mapped_direct:
            continue
        hits = [keyword for keyword in item["keywords"] if normalize_key(keyword) and normalize_key(keyword) in normalize_key(evidence)]
        if hits:
            inferred.append({"skill": item["name"], "confidence": round(min(0.85, 0.55 + 0.1 * (len(hits) - 1)), 2), "evidence": hits, "review_required": True})
    record["direct_skills"] = mapped_direct or None
    record["inferred_skills"] = inferred or None
    record["skills"] = list(dict.fromkeys([*mapped_direct, *(item["skill"] for item in inferred)])) or None
    return record
