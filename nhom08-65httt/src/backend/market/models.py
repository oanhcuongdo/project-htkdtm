from django.db import models
from django.db.models import Q


class Source(models.Model):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=120)

    class Meta:
        db_table = "market_source"


class RawDocument(models.Model):
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    source_url = models.URLField(max_length=500)
    content_hash = models.CharField(max_length=64)
    payload = models.BinaryField()
    first_collected_at = models.DateTimeField()

    class Meta:
        db_table = "raw_document"
        constraints = [
            models.UniqueConstraint(
                fields=["source", "source_url", "content_hash"], name="raw_document_identity"
            ),
        ]


class CollectionRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    source_url = models.URLField(max_length=500)
    raw_document = models.ForeignKey(RawDocument, null=True, on_delete=models.PROTECT)
    started_at = models.DateTimeField(auto_now_add=True)
    collected_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=12, choices=Status, default=Status.RUNNING)
    http_status = models.PositiveSmallIntegerField(null=True)
    rows_received = models.PositiveIntegerField(default=0)
    created_count = models.PositiveIntegerField(default=0)
    revised_count = models.PositiveIntegerField(default=0)
    unchanged_count = models.PositiveIntegerField(default=0)
    rejected_count = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)

    class Meta:
        db_table = "raw_collection_run"


class QualityIssue(models.Model):
    run = models.ForeignKey(CollectionRun, related_name="issues", on_delete=models.PROTECT)
    line = models.CharField(max_length=500)
    reason = models.CharField(max_length=200)

    class Meta:
        db_table = "raw_quality_issue"


class PriceSeries(models.Model):
    class PriceType(models.TextChoices):
        INDICATOR = "indicator", "Chỉ báo"
        DOMESTIC = "domestic", "Nội địa"
        FUTURES_REPUBLISHED = "futures_republished", "Kỳ hạn công bố lại"

    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    code = models.SlugField(max_length=60)
    name = models.CharField(max_length=120)
    commodity = models.CharField(max_length=40)
    price_type = models.CharField(max_length=24, choices=PriceType)
    market = models.CharField(max_length=80)
    contract_code = models.CharField(max_length=30, blank=True)
    currency = models.CharField(max_length=3)
    unit = models.CharField(max_length=24)

    class Meta:
        db_table = "dw_price_series"
        constraints = [
            models.UniqueConstraint(fields=["source", "code"], name="price_series_identity"),
        ]


class PriceObservation(models.Model):
    series = models.ForeignKey(PriceSeries, on_delete=models.PROTECT)
    run = models.ForeignKey(CollectionRun, on_delete=models.PROTECT)
    effective_date = models.DateField()
    value = models.DecimalField(max_digits=14, decimal_places=4)
    revision = models.PositiveIntegerField(default=1)
    is_current = models.BooleanField(default=True)

    class Meta:
        db_table = "dw_price_observation"
        constraints = [
            models.UniqueConstraint(
                fields=["series", "effective_date", "revision"], name="price_revision_identity"
            ),
            models.UniqueConstraint(
                fields=["series", "effective_date"],
                condition=Q(is_current=True),
                name="price_one_current_revision",
            ),
            models.CheckConstraint(condition=Q(value__gt=0), name="price_value_positive"),
            models.CheckConstraint(condition=Q(revision__gte=1), name="price_revision_positive"),
        ]
        indexes = [models.Index(fields=["-effective_date", "id"], condition=Q(is_current=True),
                                name="price_current_date_idx")]


class ExchangeRateObservation(models.Model):
    class RateType(models.TextChoices):
        CASH_BUY = "cash_buy", "Mua tiền mặt"
        TRANSFER_BUY = "transfer_buy", "Mua chuyển khoản"
        SELL = "sell", "Bán"

    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    run = models.ForeignKey(CollectionRun, on_delete=models.PROTECT)
    currency_code = models.CharField(max_length=3)
    currency_name = models.CharField(max_length=100)
    rate_type = models.CharField(max_length=16, choices=RateType)
    effective_at = models.DateTimeField()
    value = models.DecimalField(max_digits=14, decimal_places=4)
    revision = models.PositiveIntegerField(default=1)
    is_current = models.BooleanField(default=True)

    class Meta:
        db_table = "dw_fx_observation"
        constraints = [
            models.UniqueConstraint(
                fields=["source", "currency_code", "rate_type", "effective_at", "revision"],
                name="fx_revision_identity",
            ),
            models.UniqueConstraint(
                fields=["source", "currency_code", "rate_type", "effective_at"],
                condition=Q(is_current=True),
                name="fx_one_current_revision",
            ),
            models.CheckConstraint(condition=Q(value__gt=0), name="fx_value_positive"),
            models.CheckConstraint(condition=Q(revision__gte=1), name="fx_revision_positive"),
        ]
        indexes = [models.Index(
            fields=["source", "currency_code", "rate_type", "-effective_at"],
            condition=Q(is_current=True),
            name="fx_current_latest_idx",
        )]
