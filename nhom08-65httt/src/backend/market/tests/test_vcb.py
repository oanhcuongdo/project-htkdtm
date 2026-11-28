from datetime import datetime, timedelta, timezone
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone as django_timezone
from market.models import CollectionRun, ExchangeRateObservation, RawDocument, Source
from market.vcb import parse_exchange_rates
from market.vcb_collection import publish_exchange_rates


SAMPLE_XML = b'''<?xml version="1.0" encoding="utf-8"?>
<ExrateList>
  <DateTime>11/27/2026 11:07:00 AM</DateTime>
  <Exrate CurrencyCode="USD" CurrencyName="US DOLLAR" Buy="25,620.00" Transfer="25,650.00" Sell="26,030.00" />
  <Exrate CurrencyCode="DKK" CurrencyName="DANISH KRONE" Buy="-" Transfer="3,725.21" Sell="3,867.76" />
</ExrateList>'''


class VietcombankXmlParserTests(SimpleTestCase):
    def test_parses_types_amounts_and_vietnam_timestamp(self):
        rates, issues = parse_exchange_rates(SAMPLE_XML)

        self.assertEqual(issues, [])
        self.assertEqual(len(rates), 5)
        self.assertEqual(rates[0][:4], ("USD", "US DOLLAR", "cash_buy", Decimal("25620.00")))
        self.assertEqual(rates[1][2:4], ("transfer_buy", Decimal("25650.00")))
        self.assertEqual(rates[2][2:4], ("sell", Decimal("26030.00")))
        self.assertEqual(rates[3][2:4], ("transfer_buy", Decimal("3725.21")))
        self.assertEqual(rates[0][4], datetime(2026, 11, 27, 11, 7, tzinfo=timezone(timedelta(hours=7))))

    def test_reports_malformed_amount_and_skips_unquoted_dash(self):
        xml = SAMPLE_XML.replace(b'Buy="25,620.00"', b'Buy="bad"')

        rates, issues = parse_exchange_rates(xml)

        self.assertEqual(len(rates), 4)
        self.assertEqual(len(issues), 1)
        self.assertIn("Invalid Buy value for USD", issues[0][1])

    def test_rejects_wrong_root_or_empty_feed(self):
        with self.assertRaisesMessage(ValueError, "root must be ExrateList"):
            parse_exchange_rates(b"<rates />")
        with self.assertRaisesMessage(ValueError, "no Exrate entries"):
            parse_exchange_rates(b"<ExrateList><DateTime>11/27/2026 11:07:00 AM</DateTime></ExrateList>")


class VietcombankDeduplicationTests(TestCase):
    def setUp(self):
        self.source = Source.objects.create(code="vietcombank", name="Vietcombank")
        self.effective_at = datetime(2026, 11, 27, 11, 7, tzinfo=timezone(timedelta(hours=7)))
        self.rates = [
            ("USD", "US DOLLAR", "cash_buy", Decimal("25620.00"), self.effective_at),
            ("USD", "US DOLLAR", "transfer_buy", Decimal("25650.00"), self.effective_at),
        ]

    def make_run(self):
        run = CollectionRun.objects.create(
            source=self.source,
            source_url="https://portal.vietcombank.com.vn/exchangerates.xml",
        )
        raw_document = RawDocument.objects.create(
            source=self.source,
            source_url=run.source_url,
            content_hash=f"{run.pk:064x}",
            payload=b"<ExrateList />",
            first_collected_at=django_timezone.now(),
        )
        run.raw_document = raw_document
        run.collected_at = django_timezone.now()
        run.save(update_fields=["raw_document", "collected_at"])
        return run

    def test_latest_rates_are_shown_on_page_and_api(self):
        publish_exchange_rates(self.make_run(), self.rates)

        page = self.client.get(reverse("exchange-rate-page"))
        api = self.client.get(reverse("exchange-rate-list"), {"currency": "usd"})

        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "USD")
        self.assertEqual(api.status_code, 200)
        response_rows = api.json()
        self.assertEqual(len(response_rows), 2)
        self.assertEqual({row["currency_code"] for row in response_rows}, {"USD"})
        self.assertEqual(response_rows[0]["source"], "vietcombank")
        self.assertRegex(response_rows[0]["content_hash"], r"^[0-9a-f]{64}$")

    def test_rerunning_same_snapshot_does_not_create_duplicate_observations(self):
        first_run = self.make_run()
        publish_exchange_rates(first_run, self.rates)
        second_run = self.make_run()
        publish_exchange_rates(second_run, self.rates)

        self.assertEqual(ExchangeRateObservation.objects.count(), 2)
        self.assertEqual(first_run.created_count, 2)
        self.assertEqual(second_run.unchanged_count, 2)
        self.assertEqual(second_run.created_count, 0)

    def test_changed_value_creates_a_revision_and_keeps_one_current_row(self):
        publish_exchange_rates(self.make_run(), self.rates)
        changed_rates = [
            ("USD", "US DOLLAR", "cash_buy", Decimal("25621.00"), self.effective_at),
        ]
        revised_run = self.make_run()
        publish_exchange_rates(revised_run, changed_rates)

        rows = ExchangeRateObservation.objects.filter(currency_code="USD", rate_type="cash_buy")
        self.assertEqual(rows.count(), 2)
        self.assertEqual(rows.filter(is_current=True).count(), 1)
        self.assertEqual(rows.get(is_current=True).revision, 2)
        self.assertEqual(revised_run.revised_count, 1)

    def test_database_constraint_rejects_duplicate_current_identity(self):
        publish_exchange_rates(self.make_run(), self.rates[:1])
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ExchangeRateObservation.objects.create(
                    source=self.source,
                    run=self.make_run(),
                    currency_code="USD",
                    currency_name="US DOLLAR",
                    rate_type="cash_buy",
                    effective_at=self.effective_at,
                    value=Decimal("25620.00"),
                    revision=2,
                )
