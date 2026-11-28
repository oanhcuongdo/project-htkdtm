from dataclasses import asdict, dataclass, fields


@dataclass
class Course:
    course_id: str = ""
    title: str = ""
    url: str = ""
    subtitle: str = ""
    instructors: str = ""
    category: str = ""
    subcategory: str = ""
    rating: str = ""
    rating_count: str = ""
    student_count: str = ""
    price: str = ""
    currency: str = ""
    original_price: str = ""
    discount: str = ""
    level: str = ""
    language: str = ""
    captions: str = ""
    last_updated: str = ""
    duration: str = ""
    lecture_count: str = ""
    section_count: str = ""
    certificate: str = ""
    image_url: str = ""
    requirements: str = ""
    learning_objectives: str = ""
    target_audience: str = ""
    scraped_at: str = ""

    @classmethod
    def columns(cls):
        return [field.name for field in fields(cls)]

    def to_dict(self):
        return {key: (value if value is not None else "") for key, value in asdict(self).items()}
