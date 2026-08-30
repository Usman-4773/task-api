from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)


def generate_pdf_report(data: dict) -> str:
    filename = REPORT_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    pdf = canvas.Canvas(str(filename), pagesize=A4)
    width, height = A4

    y = height - 60

    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(50, y, "Task Summary Report")

    y -= 40
    pdf.setFont("Helvetica", 12)

    pdf.drawString(50, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    y -= 40

    for key, value in data.items():
        pdf.drawString(50, y, f"{key}: {value}")
        y -= 25

    pdf.save()

    return str(filename)