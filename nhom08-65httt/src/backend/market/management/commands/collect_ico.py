import re
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from market import ico
from market.collection import collect_ico


class Command(BaseCommand):
    help = "Download the ICO daily indicator PDF, retain raw data and publish valid prices."

    def add_arguments(self, parser):
        parser.add_argument("--month", help="ICO archive month in YYYY-MM format")

    def handle(self, *args, **options):
        month_arg = options["month"]
        expected_month = None
        url = ico.CURRENT_URL
        if month_arg:
            try:
                if not re.fullmatch(r"[0-9]{4}-[0-9]{2}", month_arg):
                    raise ValueError
                archive_date = date.fromisoformat(f"{month_arg}-01")
            except ValueError as error:
                raise CommandError("--month must be a valid YYYY-MM") from error
            expected_month = (archive_date.year, archive_date.month)
            url = ico.ARCHIVE_URL.format(year=archive_date.year, month=archive_date.month)
        try:
            run = collect_ico(url, expected_month)
        except Exception as error:
            raise CommandError(f"ICO collection failed: {error}") from error
        self.stdout.write(
            f"run={run.pk} http={run.http_status} raw={run.raw_document_id} "
            f"rows={run.rows_received} rejected_rows={run.rejected_count} "
            f"created_prices={run.created_count} revised_prices={run.revised_count} "
            f"unchanged_prices={run.unchanged_count}"
        )
