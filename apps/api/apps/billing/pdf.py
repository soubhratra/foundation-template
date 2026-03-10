"""
Invoice PDF rendering via WeasyPrint + Jinja2.

Usage:
    from apps.billing.pdf import render_invoice_pdf

    pdf_bytes = render_invoice_pdf({
        "reference": "PAY-42",
        "date": "2026-03-10",
        "customer_email": "user@example.com",
        "description": "Pro Monthly",
        "amount": 29.00,
        "currency": "usd",
    })

Notes:
    - weasyprint is imported INSIDE render_invoice_pdf() to avoid Celery worker
      fork issues (WeasyPrint issue #684 — fontconfig initializes on import and
      can deadlock in a forked process if initialized before the fork).
    - Jinja2 templates are loaded from the billing app's templates/ directory.
    - MAX_PDF_BYTES cap (512 KB) guards against runaway rendering.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

# 512 KB ceiling — single invoice pages should never approach this limit.
MAX_PDF_BYTES = 512 * 1024

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def render_invoice_pdf(invoice_data: dict) -> bytes:
    """Render an invoice dict to PDF bytes.

    Args:
        invoice_data: Dict with keys: reference, date, customer_email,
                      description, amount (float), currency (str).

    Returns:
        bytes: Raw PDF bytes starting with b"%PDF".

    Raises:
        ValueError: If the rendered PDF exceeds MAX_PDF_BYTES (512 KB).
    """
    # Lazy import: weasyprint must NOT be imported at module load time.
    # See module docstring for rationale.
    import weasyprint  # noqa: PLC0415

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("billing/invoice.html.j2")
    html_string = template.render(invoice=invoice_data)

    pdf_bytes: bytes = weasyprint.HTML(string=html_string).write_pdf()

    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise ValueError(
            f"Generated PDF is {len(pdf_bytes)} bytes, which exceeds the "
            f"{MAX_PDF_BYTES}-byte limit. Template may be too large."
        )

    return pdf_bytes
