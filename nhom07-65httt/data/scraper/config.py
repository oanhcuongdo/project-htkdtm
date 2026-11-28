from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Config:
    start_url: str = "https://www.udemy.com/courses/"
    crawl_mode: str = "sitemap"
    sitemap_url: str = "https://www.udemy.com/sitemap.xml"
    output_file: str = "data/udemy_courses.csv"
    start_page: int = 1
    max_pages: int = 1
    max_courses: int = 0
    max_total_courses: int = 0
    append: bool = False
    request_delay: float = 2.0
    timeout: int = 30
    retries: int = 3
    respect_robots_txt: bool = True
    source_authorized: bool = False
    authorization_reference: str | None = None
    user_agent: str = "PublicCourseResearch/1.0"

    @classmethod
    def load(cls, path: str | Path):
        source = Path(path)
        values = yaml.safe_load(source.read_text(encoding="utf-8")) if source.exists() else {}
        values = values or {}
        known = cls.__dataclass_fields__
        return cls(**{key: value for key, value in values.items() if key in known})
