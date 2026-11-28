from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit


def check_quality(record: dict) -> dict:
    flags = list(record.get("quality_flags") or [])
    if not record.get("description"):
        flags.append("missing_description")
    if not record.get("skills"):
        flags.append("missing_skills")
    if not record.get("level"):
        flags.append("missing_level")
    amount = record.get("price_amount")
    if amount is not None:
        try:
            if not Decimal(str(amount)).is_finite() or Decimal(str(amount)) < 0:
                flags.append("invalid_price")
        except InvalidOperation:
            flags.append("invalid_price")
    url = record.get("canonical_url")
    parts = urlsplit(url or "")
    valid_url = parts.scheme == "https" and parts.hostname == "www.udemy.com" and parts.path.startswith("/course/")
    if not valid_url:
        flags.append("broken_url")
    if not record.get("title"):
        flags.append("missing_title")
    if not record.get("source_course_id") or not record.get("source_name"):
        flags.append("missing_source_identity")
    if record.get("duplicate_status") == "exact_duplicate":
        flags.append("exact_duplicate")
    if record.get("inferred_skills"):
        flags.append("inferred_skills_review")
    flags = list(dict.fromkeys(flags))
    reject_flags = {"broken_url", "missing_title", "missing_source_identity", "exact_duplicate"}
    if reject_flags.intersection(flags):
        status = "rejected"
    elif flags:
        status = "needs_review"
    else:
        status = "approved_candidate"
    record["quality_status"] = status
    record["quality_flags"] = flags
    return record
