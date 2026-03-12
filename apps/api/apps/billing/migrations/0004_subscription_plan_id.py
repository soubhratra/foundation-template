from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0003_fix_stub_pro_monthly_price_id"),
    ]
    operations = [
        migrations.AddField(
            model_name="subscription",
            name="plan_id",
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
    ]
