from hashlib import sha256

import requests
from django.db import connection, transaction
from django.utils import timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from market import ico
from market.models import CollectionRun, PriceObservation, PriceSeries, QualityIssue, RawDocument, Source

MAX_PDF_BYTES = 5 * 1024 * 1024
ICO_LOCK_KEY = 813001


def collect_ico(source_url, expected_month=None):
    # A session lock spans the download and commits raw before attempting the ETL.
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [ICO_LOCK_KEY])
        locked = cursor.fetchone()[0]
        if not locked:
            raise RuntimeError("An ICO collection is already running")
        try:
            source, _ = Source.objects.get_or_create(
                code="ico", defaults={"name": "International Coffee Organization (ICO)"}
            )
            run = CollectionRun.objects.create(source=source, source_url=source_url)
            try:
                payload = download_pdf(run)
                rows, issues = ico.parse_daily_prices(
                    payload, timezone.localdate(run.collected_at), expected_month
                )
                run.rows_received = len(rows) + len(issues)
                run.rejected_count = len(issues)
                QualityIssue.objects.bulk_create(
                    QualityIssue(run=run, line=line[:500], reason=reason[:200])
                    for line, reason in issues
                )
                if not rows:
                    raise ValueError("The ICO PDF contains no valid daily prices")
                publish_prices(run, rows)
            except Exception as error:
                run.status = CollectionRun.Status.FAILED
                run.error = f"{type(error).__name__}: {error}"[:2000]
                run.finished_at = timezone.now()
                run.save(update_fields=["status", "error", "finished_at", "rows_received", "rejected_count"])
                raise
            return run
        finally:
            cursor.execute("SELECT pg_advisory_unlock(%s)", [ICO_LOCK_KEY])


def download_pdf(run):
    retry = Retry(
        total=2, backoff_factor=0.5, status_forcelist=(500, 502, 503, 504),
        allowed_methods={"GET"}, raise_on_status=False, respect_retry_after_header=False
    )
    with requests.Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=retry))
        with session.get(run.source_url, timeout=(5, 15), stream=True) as response:
            run.http_status = response.status_code
            run.save(update_fields=["http_status"])
            response.raise_for_status()
            payload = bytearray()
            for chunk in response.iter_content(chunk_size=64 * 1024):
                payload.extend(chunk)
                if len(payload) > MAX_PDF_BYTES:
                    raise ValueError("ICO response exceeds the collection size limit")
    payload = bytes(payload)
    run.collected_at = timezone.now()
    run.raw_document, _ = RawDocument.objects.get_or_create(
        source=run.source,
        source_url=run.source_url,
        content_hash=sha256(payload).hexdigest(),
        defaults={"payload": payload, "first_collected_at": run.collected_at},
    )
    run.save(update_fields=["collected_at", "raw_document"])
    if not payload.startswith(b"%PDF-"):
        raise ValueError("ICO response is not a PDF")
    return payload


@transaction.atomic
def publish_prices(run, rows):
    series_list = [
        PriceSeries.objects.get_or_create(
            source=run.source, code=code,
            defaults={
                "name": name, "commodity": commodity, "price_type": PriceSeries.PriceType.INDICATOR,
                "market": "global", "currency": "USD", "unit": "usd_cent_per_lb",
            },
        )[0]
        for code, name, commodity in ico.SERIES
    ]
    current = {
        (item.series_id, item.effective_date): item
        for item in PriceObservation.objects.filter(
            series__in=series_list,
            effective_date__in=[effective_date for effective_date, _ in rows],
            is_current=True,
        )
    }
    for effective_date, values in rows:
        for series, value in zip(series_list, values, strict=True):
            previous = current.get((series.pk, effective_date))
            if previous and previous.value == value:
                run.unchanged_count += 1
                continue
            revision = 1
            if previous:
                previous.is_current = False
                previous.save(update_fields=["is_current"])
                revision = previous.revision + 1
                run.revised_count += 1
            else:
                run.created_count += 1
            PriceObservation.objects.create(
                series=series, effective_date=effective_date, value=value, run=run, revision=revision
            )
    run.status = CollectionRun.Status.SUCCEEDED
    run.finished_at = timezone.now()
    run.save(update_fields=[
        "status", "finished_at", "rows_received", "rejected_count",
        "created_count", "revised_count", "unchanged_count",
    ])
