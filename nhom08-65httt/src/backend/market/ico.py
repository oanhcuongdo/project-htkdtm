import re
from collections import Counter
from datetime import date
from decimal import Decimal
from io import BytesIO

import pdfplumber

CURRENT_URL = "https://ico.org/documents/I-CIP.pdf"
ARCHIVE_URL = "https://ico.org/documents/prices/I-CIP_{month:02d}.{year:04d}.pdf"
SERIES = (
    ("i-cip", "I-CIP tổng hợp", "coffee"),
    ("colombian-milds", "Colombian Milds", "arabica"),
    ("other-milds", "Other Milds", "arabica"),
    ("brazilian-naturals", "Brazilian Naturals", "arabica"),
    ("robustas", "Robustas", "robusta"),
)
MONTHS = "January February March April May June July August September October November December".split()
TITLE = re.compile(r"^ICO Indicator Prices\s*-\s*([A-Za-z]+) (\d{4}) \(I-CIP\)$", re.MULTILINE)
HEADER = re.compile(r"^In US cents/lb\s+Colombian Brazilian\s+I-CIP Other Milds Robustas\s+Milds Naturals$", re.MULTILINE)
DAY = re.compile(r"^(\d{1,2})-([A-Za-z]{3})(?=\s|$)")
NUMBER = re.compile(r"[0-9]{1,8}\.[0-9]{2}")


def parse_daily_prices(payload, latest_date, expected_month=None):
    with pdfplumber.open(BytesIO(payload)) as pdf:
        document = "\n".join(page.extract_text() or "" for page in pdf.pages)
    title = TITLE.search(document)
    if title is None or not HEADER.search(document) or title[1] not in MONTHS:
        raise ValueError("Unrecognized ICO title, units, or price columns")
    month, year = MONTHS.index(title[1]) + 1, int(title[2])
    if expected_month and (year, month) != expected_month:
        raise ValueError("ICO PDF month differs from the requested archive")

    candidates = []
    issues = []
    for line in document.splitlines():
        match = DAY.match(line)
        if not match:
            continue
        values = line[match.end():].split()
        if not values:
            continue  # The current PDF lists days with no published values.
        try:
            effective_date = date(year, month, int(match[1]))
            if match[2] != MONTHS[month - 1][:3] or effective_date > latest_date:
                raise ValueError("Day is outside the reported month or in the future")
            if len(values) != len(SERIES) or not all(NUMBER.fullmatch(value) for value in values):
                raise ValueError("Expected five prices in US cents/lb")
            prices = tuple(Decimal(value) for value in values)
            if any(value <= 0 for value in prices):
                raise ValueError("Price must be positive")
        except ValueError as error:
            issues.append((line, str(error)))
        else:
            candidates.append((effective_date, prices, line))

    counts = Counter(effective_date for effective_date, _, _ in candidates)
    rows = []
    for effective_date, prices, line in candidates:
        if counts[effective_date] == 1:
            rows.append((effective_date, prices))
        else:
            issues.append((line, "Duplicate date in the ICO PDF"))
    return rows, issues
