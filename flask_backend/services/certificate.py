from datetime import date, datetime, timezone
from pathlib import Path
from flask import current_app
from models import db, Internship, Certificate, CertificateSequence
from .pdf import snapshot_data, render_certificate_pdf


def generate_certificate(internship_id):
    """
    Generate certificate for an internship:
    - Verifies internship is completed with valid end date
    - Increments CertificateSequence for current year
    - Formats certificate_id 'INT-YYYY-XXXXX'
    - Creates Certificate entry and generates PDF file
    - Sets internship status to 'CERTIFICATE_ISSUED'
    """
    internship = Internship.query.get(internship_id)
    if not internship:
        raise ValueError("Internship not found.")

    if internship.certificate:
        raise ValueError("Certificate has already been generated.")

    if not internship.end_date:
        raise ValueError("Please set the internship end date before generating the certificate.")

    if internship.status != "COMPLETED":
        internship.status = "COMPLETED"
        internship.completed_at = datetime.now(timezone.utc)

    data = snapshot_data(internship)
    today = date.today()

    # Get or create sequence for current year
    sequence = CertificateSequence.query.filter_by(year=today.year).with_for_update().first()
    if not sequence:
        sequence = CertificateSequence(year=today.year, value=0)
        db.session.add(sequence)
        db.session.flush()

    sequence.value += 1
    cert_id = f"INT-{today.year}-{sequence.value:05d}"

    cert = Certificate(
        internship=internship,
        certificate_id=cert_id,
        issue_date=today,
        snapshot=data,
        status="VALID",
    )
    db.session.add(cert)
    db.session.flush()

    # Render PDF
    verification_url = f"{current_app.config['FRONTEND_BASE_URL']}/verify/{cert.verification_token}"
    pdf_bytes = render_certificate_pdf(data, today, cert.certificate_id, verification_url)

    # Save PDF to media/certificates/
    media_folder = Path(current_app.config["MEDIA_FOLDER"])
    cert_folder = media_folder / "certificates"
    cert_folder.mkdir(parents=True, exist_ok=True)

    pdf_filename = f"{cert.certificate_id}.pdf"
    file_path = cert_folder / pdf_filename
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)

    cert.pdf_file = f"certificates/{pdf_filename}"
    internship.status = "CERTIFICATE_ISSUED"

    db.session.commit()
    return cert
