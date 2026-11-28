import os

from django.core.management.base import BaseCommand, CommandError

from market.vcb_collection import DEFAULT_XML_URL, collect_vcb


class Command(BaseCommand):
    help = "Download Vietcombank exchange-rate XML, retain raw data and publish rates."

    def add_arguments(self, parser):
        parser.add_argument("--url", default=os.environ.get("VCB_XML_URL", DEFAULT_XML_URL))

    def handle(self, *args, **options):
        try:
            run = collect_vcb(options["url"])
        except Exception as error:
            raise CommandError(f"Vietcombank collection failed: {error}") from error
        self.stdout.write(
            f"run={run.pk} http={run.http_status} raw={run.raw_document_id} "
            f"rows={run.rows_received} rejected_rows={run.rejected_count} "
            f"created_rates={run.created_count} revised_rates={run.revised_count} "
            f"unchanged_rates={run.unchanged_count}"
        )
