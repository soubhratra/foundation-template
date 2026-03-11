"""
Data migration: fix PlanProviderMapping for stub pro/monthly.

StubAdapter.retrieve_subscription() returns {"current_price_id": "price_stub_monthly"}
for every subscription.  Migration 0002 seeded the pro/monthly row with
"price_stub_pro_monthly", which never matches the adapter response, so
get_subscription_detail() always returns plan_id=None for stub users.

This migration updates the existing row to use "price_stub_monthly" so that
the plan_id lookup succeeds in development and test environments.
"""

from django.db import migrations


def fix_pro_monthly_price_id(apps, schema_editor):
    PlanProviderMapping = apps.get_model("billing", "PlanProviderMapping")
    PlanProviderMapping.objects.filter(
        plan_id="pro",
        provider="stub",
        billing_period="monthly",
    ).update(price_id="price_stub_monthly")


def revert_pro_monthly_price_id(apps, schema_editor):
    PlanProviderMapping = apps.get_model("billing", "PlanProviderMapping")
    PlanProviderMapping.objects.filter(
        plan_id="pro",
        provider="stub",
        billing_period="monthly",
    ).update(price_id="price_stub_pro_monthly")


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0002_plan_provider_mapping_stub_seed"),
    ]

    operations = [
        migrations.RunPython(fix_pro_monthly_price_id, reverse_code=revert_pro_monthly_price_id),
    ]
