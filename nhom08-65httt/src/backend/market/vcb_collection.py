from hashlib import sha256

import requests
from django.db import connection, transaction
from django.utils import timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from market.models import (
    CollectionRun,
    ExchangeRateObservation,
    QualityIssue,
    RawDocument,
    Source,
)
from market.vcb import parse_exchange_rates

DEFAULT_XML_URL = "https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx?b=10"
MAX_XML_BYTES = 2 * 1024 * 1024
VCB_LOCK_KEY = 813002


def collect_vcb(source_url=DEFAULT_XML_URL):
    """Fetch, retain and publish one Vietcombank XML snapshot."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [VCB_LOCK_KEY])
        locked = cursor.fetchone()[0]
        if not locked:
            raise RuntimeError("A Vietcombank collection is already running")
        try:
            source, _ = Source.objects.get_or_create(
                code="vietcombank", defaults={"name": "Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank)"}
            )
            run = CollectionRun.objects.create(source=source, source_url=source_url)
            try:
                payload = download_xml(run)
                rows, issues = parse_exchange_rates(payload)
                run.rows_received = len(rows) + len(issues)
                run.rejected_count = len(issues)
                QualityIssue.objects.bulk_create(
                    QualityIssue(run=run, line=line[:500], reason=reason[:200])
                    for line, reason in issues
                )
                publish_exchange_rates(run, rows)
            except Exception as error:
                run.status = CollectionRun.Status.FAILED
                run.error = f"{type(error).__name__}: {error}"[:2000]
                run.finished_at = timezone.now()
                run.save(update_fields=[
                    "status", "error", "finished_at", "rows_received", "rejected_count",
                    "http_status", "collected_at", "raw_document",
                ])
                raise
            return run
        finally:
            cursor.execute("SELECT pg_advisory_unlock(%s)", [VCB_LOCK_KEY])


def download_xml(run):
    retry = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods={"GET"},
        raise_on_status=False,
        respect_retry_after_header=False,
    )
    with requests.Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=retry))
        with session.get(
            run.source_url,
            headers={"Accept": "application/xml, text/xml;q=0.9, */*;q=0.1"},
            timeout=(5, 15),
            stream=True,
        ) as response:
            run.http_status = response.status_code
            run.save(update_fields=["http_status"])
            response.raise_for_status()
            payload = bytearray()
            for chunk in response.iter_content(chunk_size=32 * 1024):
                payload.extend(chunk)
                if len(payload) > MAX_XML_BYTES:
                    raise ValueError("Vietcombank response exceeds the 2 MiB size limit")
    payload = bytes(payload)
    run.collected_at = timezone.now()
    run.raw_document, _ = RawDocument.objects.get_or_create(
        source=run.source,
        source_url=run.source_url,
        content_hash=sha256(payload).hexdigest(),
        defaults={"payload": payload, "first_collected_at": run.collected_at},
    )
    run.save(update_fields=["collected_at", "raw_document"])
    return payload


@transaction.atomic
def publish_exchange_rates(run, rows):
    keys = {(code, rate_type, effective_at) for code, _, rate_type, _, effective_at in rows}
    current = {
        (item.currency_code, item.rate_type, item.effective_at): item
        for item in ExchangeRateObservation.objects.filter(
            source=run.source,
            is_current=True,
            currency_code__in={code for code, _, _ in keys},
            rate_type__in={rate_type for _, rate_type, _ in keys},
            effective_at__in={effective_at for _, _, effective_at in keys},
        )
    }
    for code, name, rate_type, value, effective_at in rows:
        previous = current.get((code, rate_type, effective_at))
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
        ExchangeRateObservation.objects.create(
            source=run.source,
            run=run,
            currency_code=code,
            currency_name=name,
            rate_type=rate_type,
            effective_at=effective_at,
            value=value,
            revision=revision,
        )
    run.status = CollectionRun.Status.SUCCEEDED
    run.finished_at = timezone.now()
    run.save(update_fields=[
        "status", "finished_at", "rows_received", "rejected_count",
        "created_count", "revised_count", "unchanged_count",
    ])
