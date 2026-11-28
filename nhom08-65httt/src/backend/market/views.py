from django.shortcuts import render
from django.db.models import F, Window
from django.db.models.functions import RowNumber
from rest_framework import generics, permissions, serializers
from rest_framework.pagination import PageNumberPagination

from market.models import ExchangeRateObservation, PriceObservation


def current_prices():
    return (
        PriceObservation.objects.filter(is_current=True)
        .select_related("series__source", "run__raw_document")
        .defer("run__raw_document__payload")
        .order_by("-effective_date", "series__code", "id")
    )


class PriceSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="series.source.code")
    source_name = serializers.CharField(source="series.source.name")
    source_url = serializers.URLField(source="run.source_url")
    collected_at = serializers.DateTimeField(source="run.collected_at")
    run_id = serializers.IntegerField(read_only=True)
    content_hash = serializers.CharField(source="run.raw_document.content_hash")
    series = serializers.CharField(source="series.code")
    series_name = serializers.CharField(source="series.name")
    commodity = serializers.CharField(source="series.commodity")
    price_type = serializers.CharField(source="series.price_type")
    market = serializers.CharField(source="series.market")
    contract_code = serializers.CharField(source="series.contract_code")
    currency = serializers.CharField(source="series.currency")
    unit = serializers.CharField(source="series.unit")

    class Meta:
        model = PriceObservation
        fields = (
            "id", "source", "source_name", "source_url", "collected_at", "content_hash",
            "run_id", "series", "series_name", "commodity", "price_type", "market",
            "contract_code", "currency", "unit", "effective_date", "value", "revision",
        )


class PricePagination(PageNumberPagination):
    page_size = 25


class PriceList(generics.ListAPIView):
    serializer_class = PriceSerializer
    pagination_class = PricePagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        prices = current_prices()
        for parameter, field in (
            ("source", "series__source__code"),
            ("series", "series__code"),
            ("price_type", "series__price_type"),
        ):
            if parameter in self.request.query_params:
                prices = prices.filter(**{field: self.request.query_params[parameter]})
        return prices


def price_page(request):
    return render(request, "market/prices.html", {"prices": current_prices()[:25]})


def latest_exchange_rates():
    return (
        ExchangeRateObservation.objects.filter(source__code="vietcombank", is_current=True)
        .select_related("source", "run__raw_document")
        .defer("run__raw_document__payload")
        .annotate(
            latest_rank=Window(
                expression=RowNumber(),
                partition_by=["source_id", "currency_code", "rate_type"],
                order_by=[F("effective_at").desc(), F("id").desc()],
            )
        )
        .filter(latest_rank=1)
        .order_by("currency_code", "rate_type")
    )


class ExchangeRateSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="source.code")
    source_name = serializers.CharField(source="source.name")
    source_url = serializers.URLField(source="run.source_url")
    collected_at = serializers.DateTimeField(source="run.collected_at")
    content_hash = serializers.CharField(source="run.raw_document.content_hash")
    rate_type_label = serializers.CharField(source="get_rate_type_display")

    class Meta:
        model = ExchangeRateObservation
        fields = (
            "id", "source", "source_name", "source_url", "collected_at", "content_hash",
            "currency_code", "currency_name", "rate_type", "rate_type_label",
            "effective_at", "value", "revision",
        )


class ExchangeRateList(generics.ListAPIView):
    serializer_class = ExchangeRateSerializer
    pagination_class = None
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        rates = latest_exchange_rates()
        currency = self.request.query_params.get("currency")
        rate_type = self.request.query_params.get("rate_type")
        if currency:
            rates = rates.filter(currency_code=currency.upper())
        if rate_type:
            rates = rates.filter(rate_type=rate_type)
        return rates


def exchange_rate_page(request):
    rows = {}
    for rate in latest_exchange_rates():
        row = rows.setdefault(rate.currency_code, {
            "currency_code": rate.currency_code,
            "currency_name": rate.currency_name,
            "cash_buy": None,
            "transfer_buy": None,
            "sell": None,
            "effective_at": rate.effective_at,
        })
        row[rate.rate_type] = rate
        if rate.effective_at > row["effective_at"]:
            row["effective_at"] = rate.effective_at
    return render(request, "market/exchange_rates.html", {"rates": list(rows.values())})
