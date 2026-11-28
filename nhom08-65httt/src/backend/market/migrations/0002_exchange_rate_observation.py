from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("market", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExchangeRateObservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("currency_code", models.CharField(max_length=3)),
                ("currency_name", models.CharField(max_length=100)),
                ("rate_type", models.CharField(choices=[("cash_buy", "Mua tiền mặt"), ("transfer_buy", "Mua chuyển khoản"), ("sell", "Bán")], max_length=16)),
                ("effective_at", models.DateTimeField()),
                ("value", models.DecimalField(decimal_places=4, max_digits=14)),
                ("revision", models.PositiveIntegerField(default=1)),
                ("is_current", models.BooleanField(default=True)),
                ("run", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="market.collectionrun")),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="market.source")),
            ],
            options={
                "db_table": "dw_fx_observation",
                "indexes": [models.Index(condition=Q(("is_current", True)), fields=["source", "currency_code", "rate_type", "-effective_at"], name="fx_current_latest_idx")],
                "constraints": [
                    models.UniqueConstraint(fields=("source", "currency_code", "rate_type", "effective_at", "revision"), name="fx_revision_identity"),
                    models.UniqueConstraint(condition=Q(("is_current", True)), fields=("source", "currency_code", "rate_type", "effective_at"), name="fx_one_current_revision"),
                    models.CheckConstraint(condition=Q(("value__gt", 0)), name="fx_value_positive"),
                    models.CheckConstraint(condition=Q(("revision__gte", 1)), name="fx_revision_positive"),
                ],
            },
        ),
    ]
