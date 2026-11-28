"""Parser for the public Vietcombank XML exchange-rate feed."""

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

VIETNAM_TIME = timezone(timedelta(hours=7), name="Asia/Ho_Chi_Minh")
RATE_ATTRIBUTES = (
    ("Buy", "cash_buy"),
    ("Transfer", "transfer_buy"),
    ("Sell", "sell"),
)
CURRENCY_CODE = re.compile(r"^[A-Z]{3}$")


def _local_name(tag):
    return tag.rsplit("}", 1)[-1]


def _parse_effective_at(value):
    value = (value or "").strip()
    formats = (
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
    )
    for date_format in formats:
        try:
            return datetime.strptime(value, date_format).replace(tzinfo=VIETNAM_TIME)
        except ValueError:
            continue
    raise ValueError("Vietcombank XML has an invalid or missing DateTime")


def parse_exchange_rates(payload):
    """Return ``(rates, issues)`` from Vietcombank's ExrateList XML.

    A rate is ``(currency_code, currency_name, rate_type, value, effective_at)``.
    A dash is a valid indication that Vietcombank does not quote that rate and
    is skipped. Malformed quoted values are returned as quality issues.
    """
    try:
        root = ET.fromstring(payload)
    except (ET.ParseError, TypeError, ValueError) as error:
        raise ValueError("Vietcombank response is not valid XML") from error

    if _local_name(root.tag) != "ExrateList":
        raise ValueError("Vietcombank XML root must be ExrateList")

    date_time = next(
        (element.text for element in root.iter() if _local_name(element.tag) == "DateTime"),
        None,
    )
    effective_at = _parse_effective_at(date_time)
    entries = [element for element in root.iter() if _local_name(element.tag) == "Exrate"]
    if not entries:
        raise ValueError("Vietcombank XML contains no Exrate entries")

    issues = []
    prepared = []
    seen_codes = set()
    duplicate_codes = set()
    for element in entries:
        code = (element.attrib.get("CurrencyCode") or "").strip().upper()
        name = (element.attrib.get("CurrencyName") or "").strip()
        line = ET.tostring(element, encoding="unicode")
        if not CURRENCY_CODE.fullmatch(code) or not name:
            issues.append((line, "Missing or invalid currency code/name"))
            continue
        if code in seen_codes:
            duplicate_codes.add(code)
            issues.append((line, f"Duplicate currency code {code} in XML"))
            continue
        seen_codes.add(code)
        prepared.append((code, name, element.attrib, line))

    rates = []
    for code, name, attributes, line in prepared:
        if code in duplicate_codes:
            continue
        for attribute, rate_type in RATE_ATTRIBUTES:
            raw_value = (attributes.get(attribute) or "").strip()
            if raw_value in ("", "-"):
                continue
            try:
                value = Decimal(raw_value.replace(",", ""))
            except InvalidOperation:
                issues.append((line, f"Invalid {attribute} value for {code}"))
                continue
            if not value.is_finite() or value <= 0 or value.as_tuple().exponent < -4:
                issues.append((line, f"{attribute} value for {code} must be positive with at most 4 decimals"))
                continue
            rates.append((code, name, rate_type, value, effective_at))

    if not rates:
        raise ValueError("Vietcombank XML contains no valid exchange rates")
    return rates, issues
