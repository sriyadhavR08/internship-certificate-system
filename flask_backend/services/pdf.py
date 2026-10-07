from datetime import date
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from flask import current_app
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode


def snapshot_data(internship):
    """
    Extract immutable snapshot dictionary for certificate issuance.
    """
    student = internship.student
    profile = student.profile
    return {
        "student_name": student.full_name,
        "gender": profile.gender if profile else "MALE",
        "candidate_type": getattr(profile, "candidate_type", "COLLEGE_INTERN") if profile else "COLLEGE_INTERN",
        "institution_name": profile.college_name if profile else "",
        "department": profile.department if profile else "",
        "course": profile.course if profile else "",
        "register_number": profile.register_number if profile else "",
        "project_name": internship.project_name,
        "start_date": internship.start_date.isoformat(),
        "end_date": internship.end_date.isoformat() if internship.end_date else None,
    }


def certificate_paragraphs(data):
    """
    Generate certificate body paragraphs.
    """
    female = data.get("gender") == "FEMALE"
    title, subject, obj, possessive = (
        ("Ms.", "she", "her", "her") if female else ("Mr.", "he", "him", "his")
    )
    name = f"<b>{title} {escape(data['student_name'])}</b>"
    project = escape(data["project_name"])
    start = date.fromisoformat(data["start_date"]).strftime("%d/%m/%Y")
    end = date.fromisoformat(data["end_date"]).strftime("%d/%m/%Y")
    return [
        f"This is to certify that {name} has completed {possessive} internship in our organization from <b>{start} to {end}</b>.",
        f"Throughout the period, {name} displayed exceptional dedication and a strong sense of responsibility, making {obj} an invaluable candidate of our project <b>“{project}”</b>.",
        f"We have no doubt that {name} will continue to excel in {possessive} future endeavours. {possessive.capitalize()} strong dedication towards continuous growth and improvement will undoubtedly lead to great success.",
        f"We wish {obj} all the best in {possessive} future career, and we are confident that {subject} will continue to make a positive impact in any role {subject} undertakes.",
    ]


def get_fonts():
    """
    Load custom fonts if present in assets/fonts directory, fallback to standard Times fonts.
    """
    assets_dir = Path(current_app.config["ASSETS_FOLDER"])
    fonts_dir = assets_dir / "fonts"
    if (fonts_dir / "LiberationSerif-Regular.ttf").exists():
        if "CertificateSerif" not in pdfmetrics.getRegisteredFontNames():
            for suffix, filename in [
                ("", "Regular"),
                ("-Bold", "Bold"),
                ("-Italic", "Italic"),
                ("-BoldItalic", "BoldItalic"),
            ]:
                pdfmetrics.registerFont(
                    TTFont(
                        "CertificateSerif" + suffix,
                        str(fonts_dir / f"LiberationSerif-{filename}.ttf"),
                    )
                )
            pdfmetrics.registerFontFamily(
                "CertificateSerif",
                normal="CertificateSerif",
                bold="CertificateSerif-Bold",
                italic="CertificateSerif-Italic",
                boldItalic="CertificateSerif-BoldItalic",
            )
        return "CertificateSerif", "CertificateSerif-Bold"
    return "Times-Roman", "Times-Bold"


def render_certificate_pdf(
    data, issue_date, certificate_id="PREVIEW", verification_url=None, mode="DIGITAL_CERTIFICATE"
):
    """
    Render high-quality A4 PDF certificate with ReportLab.
    """
    output = BytesIO()
    c = canvas.Canvas(output, pagesize=A4)
    c.setTitle(f"Wingroo Internship Certificate - {certificate_id}")
    c.setAuthor("Wingroo")
    width, height = A4
    regular, bold = get_fonts()

    # Draw logo
    if mode == "DIGITAL_CERTIFICATE":
        assets_dir = Path(current_app.config["ASSETS_FOLDER"])
        logo = assets_dir / "WINGROO.jpeg"
        if logo.exists():
            c.drawImage(
                str(logo),
                (width - 190) / 2,
                height - 165,
                width=190,
                height=127,
                preserveAspectRatio=True,
                mask="auto",
            )

    # Watermark for preview
    if certificate_id == "PREVIEW":
        c.saveState()
        c.setFillColorRGB(0.78, 0.79, 0.82)
        c.setFont("Helvetica-Bold", 42)
        c.translate(width / 2, height / 2)
        c.rotate(35)
        c.drawCentredString(0, 0, "PREVIEW - NOT VALID")
        c.restoreState()

    c.setFont(bold, 16)
    c.drawCentredString(width / 2, height - 213, "TO WHOMSOEVER IT MAY CONCERN")

    text = certificate_paragraphs(data)
    for size in [14, 13.5, 13, 12.5, 12]:
        style = ParagraphStyle(
            "body",
            fontName=regular,
            fontSize=size,
            leading=size * 1.28,
            alignment=TA_JUSTIFY,
            firstLineIndent=36,
        )
        blocks = [Paragraph(t, style) for t in text]
        heights = [block.wrap(width - 144, height)[1] for block in blocks]
        if sum(heights) + 14 * (len(blocks) - 1) <= 355:
            break
    else:
        raise ValueError("Certificate text is too long for one page. Please shorten name or project title.")

    y = height - 247
    for block, block_height in zip(blocks, heights):
        block.drawOn(c, 72, y - block_height)
        y -= block_height + 14

    c.setFont(regular, 14)
    c.drawString(72, 191, issue_date.strftime("%d/%m/%Y"))
    c.drawString(72, 170, "Coimbatore")
    c.drawRightString(width - 72, 142, "Mrs. Lincy Karthipan")
    c.setFont(regular, 12)
    c.drawRightString(width - 72, 123, "Managing Director")

    # QR Code
    if verification_url:
        qr = qrcode.make(verification_url, box_size=8, border=4)
        image = BytesIO()
        qr.save(image, format="PNG")
        image.seek(0)
        c.drawImage(ImageReader(image), 72, 63, width=76, height=76)
    else:
        c.setStrokeColorRGB(0.6, 0.6, 0.6)
        c.rect(76, 67, 68, 68)
        c.setFont("Helvetica", 9)
        c.drawCentredString(110, 100, "QR preview")

    c.setFont("Helvetica", 8)
    c.drawString(72, 52, "Scan to Verify")
    c.drawRightString(width - 72, 52, f"Certificate ID: {certificate_id}")
    c.showPage()
    c.save()
    return output.getvalue()
