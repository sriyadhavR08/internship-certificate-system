from io import BytesIO
from pathlib import Path
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from rest_framework.exceptions import ValidationError
import qrcode
from .content import paragraphs


def fonts():
    directory = Path(settings.BASE_DIR).parent / 'assets' / 'fonts'
    if (directory / 'LiberationSerif-Regular.ttf').exists():
        if 'CertificateSerif' not in pdfmetrics.getRegisteredFontNames():
            for suffix, filename in [('', 'Regular'), ('-Bold', 'Bold'), ('-Italic', 'Italic'), ('-BoldItalic', 'BoldItalic')]:
                pdfmetrics.registerFont(TTFont('CertificateSerif' + suffix, str(directory / f'LiberationSerif-{filename}.ttf')))
            pdfmetrics.registerFontFamily('CertificateSerif', normal='CertificateSerif', bold='CertificateSerif-Bold', italic='CertificateSerif-Italic', boldItalic='CertificateSerif-BoldItalic')
        return 'CertificateSerif', 'CertificateSerif-Bold'
    return 'Times-Roman', 'Times-Bold'


def render_pdf(data, issue_date, certificate_id='PREVIEW', verification_url=None, mode='DIGITAL_CERTIFICATE'):
    if mode not in ['DIGITAL_CERTIFICATE', 'BOND_SHEET_PRINT']:
        raise ValueError('Unknown layout mode')
    output = BytesIO()
    c = canvas.Canvas(output, pagesize=A4)
    c.setTitle(f'Wingroo Internship Certificate - {certificate_id}')
    c.setAuthor('Wingroo')
    width, height = A4
    regular, bold = fonts()
    if mode == 'DIGITAL_CERTIFICATE':
        logo = Path(settings.BASE_DIR).parent / 'assets' / 'WINGROO.jpeg'
        c.drawImage(str(logo), (width-190)/2, height-165, width=190, height=127, preserveAspectRatio=True, mask='auto')
    if certificate_id == 'PREVIEW':
        c.saveState()
        c.setFillColorRGB(.78, .79, .82)
        c.setFont('Helvetica-Bold', 42)
        c.translate(width/2, height/2)
        c.rotate(35)
        c.drawCentredString(0, 0, 'PREVIEW - NOT VALID')
        c.restoreState()
    c.setFont(bold, 16)
    c.drawCentredString(width/2, height-213, 'TO WHOMSOEVER IT MAY CONCERN')
    text = paragraphs(data)
    # Keep the reference's 14 pt body; reduce modestly only for longer dynamic fields.
    for size in [14, 13.5, 13, 12.5, 12]:
        style = ParagraphStyle('body', fontName=regular, fontSize=size, leading=size*1.28, alignment=TA_JUSTIFY, firstLineIndent=36)
        blocks = [Paragraph(t, style) for t in text]
        heights = [block.wrap(width-144, height)[1] for block in blocks]
        if sum(heights) + 14*(len(blocks)-1) <= 355:
            break
    else:
        raise ValidationError('Certificate text is too long for one page. Shorten the name or project title.')
    y = height-247
    for block, block_height in zip(blocks, heights):
        block.drawOn(c, 72, y-block_height)
        y -= block_height + 14
    c.setFont(regular, 14)
    c.drawString(72, 191, issue_date.strftime('%d/%m/%Y'))
    c.drawString(72, 170, 'Coimbatore')
    c.drawRightString(width-72, 142, 'Mrs. Lincy Karthipan')
    c.setFont(regular, 12)
    c.drawRightString(width-72, 123, 'Managing Director')
    if verification_url:
        qr = qrcode.make(verification_url, box_size=8, border=4)
        image = BytesIO()
        qr.save(image, format='PNG')
        image.seek(0)
        c.drawImage(ImageReader(image), 72, 63, width=76, height=76)
    else:
        c.setStrokeColorRGB(.6,.6,.6)
        c.rect(76, 67, 68, 68)
        c.setFont('Helvetica', 9)
        c.drawCentredString(110, 100, 'QR preview')
    c.setFont('Helvetica', 8)
    c.drawString(72, 52, 'Scan to Verify')
    c.drawRightString(width-72, 52, f'Certificate ID: {certificate_id}')
    c.showPage()
    c.save()
    return output.getvalue()
