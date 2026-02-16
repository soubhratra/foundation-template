import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from config.urls import api


class Command(BaseCommand):
    help = "Export the OpenAPI schema to a JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            help="Output file path (defaults to packages/api-client/openapi.json)",
        )

    def handle(self, *args, **options):
        output_arg = options.get("output")
        if output_arg:
            output_path = Path(output_arg)
        else:
            output_path = (
                settings.BASE_DIR.parent.parent
                / "packages"
                / "api-client"
                / "openapi.json"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        schema = api.get_openapi_schema()
        output_path.write_text(
            json.dumps(schema, indent=2),
            encoding="utf-8",
        )
        self.stdout.write(f"OpenAPI schema written to {output_path}")
