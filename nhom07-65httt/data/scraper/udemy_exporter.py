import csv
from pathlib import Path

from .udemy_models import Course


def existing_course_urls(output_file: str) -> set[str]:
    destination = Path(output_file)
    if not destination.exists() or destination.stat().st_size == 0:
        return set()
    with destination.open(encoding="utf-8-sig", newline="") as stream:
        return {row.get("url", "") for row in csv.DictReader(stream) if row.get("url")}


def count_course_rows(output_file: str) -> int:
    destination = Path(output_file)
    if not destination.exists() or destination.stat().st_size == 0:
        return 0
    with destination.open(encoding="utf-8-sig", newline="") as stream:
        return sum(1 for _ in csv.DictReader(stream))


def export_courses_csv(courses, output_file: str, append: bool = False) -> Path:
    destination = Path(output_file)
    destination.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    has_content = append and destination.exists() and destination.stat().st_size > 0
    if has_content:
        existing = existing_course_urls(output_file)
    mode = "a" if has_content else "w"
    with destination.open(mode, encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=Course.columns(), extrasaction="ignore")
        if not has_content:
            writer.writeheader()
        for course in courses:
            row = course.to_dict() if isinstance(course, Course) else Course(**course).to_dict()
            if row["url"] and row["url"] in existing:
                continue
            writer.writerow(row)
            if row["url"]:
                existing.add(row["url"])
    return destination


def append_course_csv(course, output_file: str) -> Path:
    destination = Path(output_file)
    destination.parent.mkdir(parents=True, exist_ok=True)
    has_content = destination.exists() and destination.stat().st_size > 0
    with destination.open("a" if has_content else "w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=Course.columns(), extrasaction="ignore")
        if not has_content:
            writer.writeheader()
        row = course.to_dict() if isinstance(course, Course) else Course(**course).to_dict()
        writer.writerow(row)
    return destination
