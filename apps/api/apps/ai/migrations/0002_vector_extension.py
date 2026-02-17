"""
Enable PGVector extension for vector similarity search.

This migration creates the pgvector extension using IF NOT EXISTS to avoid
permission errors in production environments where the extension may be
pre-installed by a database administrator.

If this migration fails with permission errors, ask your database admin to run:
    CREATE EXTENSION IF NOT EXISTS vector;
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ai", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector",
            reverse_sql="DROP EXTENSION IF EXISTS vector",
        ),
    ]
