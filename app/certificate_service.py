from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "generated"
OUTPUT_DIR.mkdir(exist_ok=True)

def safe_filename(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name).strip("_")
    return cleaned[:100] or "recipient"

def generate_certificate(job_id: int, certificate_id: int, recipient_name: str, course_name: str, event_date: str) -> str:
    # Predefined single certificate design.
    path = OUTPUT_DIR / f"certificate_{job_id}_{certificate_id}_{safe_filename(recipient_name)}.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    c.setLineWidth(3)
    c.rect(40, 40, width - 80, height - 80)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, height - 150, "CERTIFICATE OF COMPLETION")
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 220, "This certificate is proudly presented to")
    c.setFont("Helvetica-Bold", 25)
    c.drawCentredString(width / 2, height - 280, recipient_name)
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 340, "for successfully completing")
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 390, course_name)
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 450, f"Event date: {event_date}")
    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(width / 2, 90, "Bulk Certificate Generator")
    c.save()
    return str(path)
