"""Print the existing slip HTML/CSS with Chrome, without a second document layout."""
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string


class BookingSlipPDFError(RuntimeError):
    """An export failed without changing the saved booking."""


def browser_binary():
    configured = getattr(settings, 'BOOKING_PDF_BROWSER_BINARY', '')
    if configured:
        executable = shutil.which(configured) or (configured if Path(configured).is_file() else None)
        if executable:
            return executable
        raise BookingSlipPDFError('Unable to export booking slip. Check BOOKING_PDF_BROWSER_BINARY on the server.')
    for name in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'chrome'):
        executable = shutil.which(name)
        if executable:
            return executable
    for environment, suffix in (
        ('PROGRAMFILES', 'Google/Chrome/Application/chrome.exe'),
        ('PROGRAMFILES(X86)', 'Google/Chrome/Application/chrome.exe'),
        ('LOCALAPPDATA', 'Google/Chrome/Application/chrome.exe'),
    ):
        root = os.environ.get(environment)
        if root and (executable := Path(root) / suffix).is_file():
            return str(executable)
    raise BookingSlipPDFError('Unable to export booking slip. Install Chrome or Chromium on the server.')


def booking_slip_pdf(slip):
    return html_document_pdf('facilities/pages/booking_slip.html', 'components/css/booking_slip.css',
                             {'slip': slip}, 'slip_styles')


def html_document_pdf(template, stylesheet_name, context, style_key):
    """Print trusted Django HTML once; both official documents reuse Chrome export."""
    executable = browser_binary()
    stylesheet = finders.find(stylesheet_name)
    if not stylesheet:
        raise BookingSlipPDFError('Unable to export booking slip. The slip stylesheet is missing.')
    try:
        html = render_to_string(template, {
            **context, 'pdf_render': True,
            # This is application-owned CSS, never uploaded or client-provided text.
            style_key: Path(stylesheet).read_text(encoding='utf-8'),
        })
        # A separate, disposable profile avoids the user's logged-in Chrome session.
        with TemporaryDirectory(prefix='campushub-slip-') as directory:
            root = Path(directory)
            document, output = root / 'slip.html', root / 'slip.pdf'
            document.write_text(html, encoding='utf-8')
            subprocess.run([
                executable, '--headless', '--disable-gpu', '--disable-background-networking',
                '--disable-extensions', '--disable-sync', '--no-first-run', '--no-default-browser-check',
                '--no-pdf-header-footer', f'--user-data-dir={root / "profile"}',
                f'--print-to-pdf={output}', document.as_uri(),
            ], check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            pdf = output.read_bytes()
            if not pdf.startswith(b'%PDF-'):
                raise BookingSlipPDFError('Unable to export booking slip. Chrome did not produce a valid PDF.')
            return pdf
    except (OSError, subprocess.SubprocessError) as error:
        raise BookingSlipPDFError('Unable to export booking slip. Please try again.') from error
