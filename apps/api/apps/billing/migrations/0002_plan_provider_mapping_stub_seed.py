"""
Data migration: seed PlanProviderMapping rows for the stub adapter.

These rows allow BillingService._resolve_price_id() to succeed in development
and test environments using StubAdapter. Stub price IDs match the values
returned by StubAdapter.retrieve_subscription() ("price_stub_monthly").

In production, replace/supplement with real Stripe price IDs via the Django
admin or a separate data migration.
"""

from django.db import migrations

STUB_MAPPINGS = [
    # (plan_id, billing_period, price_id)
    ("pro", "monthly", "price_stub_pro_monthly"),
    ("pro", "annual", "price_stub_pro_annual"),
    ("enterprise", "monthly", "price_stub_enterprise_monthly"),
    ("enterprise", "annual", "price_stub_enterprise_annual"),
]


def seed_stub_mappings(apps, schema_editor):
    PlanProviderMapping = apps.get_model("billing", "PlanProviderMapping")
    for plan_id, billing_period, price_id in STUB_MAPPINGS:
        PlanProviderMapping.objects.get_or_create(
            plan_id=plan_id,
            provider="stub",
            billing_period=billing_period,
            defaults={"price_id": price_id, "is_active": True},
        )


def remove_stub_mappings(apps, schema_editor):
    PlanProviderMapping = apps.get_model("billing", "PlanProviderMapping")
    PlanProviderMapping.objects.filter(provider="stub").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_stub_mappings, reverse_code=remove_stub_mappings),
    ]
