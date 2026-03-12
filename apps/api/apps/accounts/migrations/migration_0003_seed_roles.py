from django.db import migrations


def seed_roles(apps, schema_editor):
    """Seed the default Django Groups used as RBAC roles.

    Uses apps.get_model() (historical model reference) as required by Django's
    migration framework. get_or_create ensures idempotency — safe to re-run.
    """
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="admin")
    Group.objects.get_or_create(name="member")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(seed_roles, migrations.RunPython.noop),
    ]
