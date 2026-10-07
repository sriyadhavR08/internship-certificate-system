from django.db import transaction
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from internships.models import Internship
from .models import Certificate, CertificateSequence
from .content import snapshot
from .layout import render_pdf


def generate(internship_id):
    saved_file = None
    try:
        with transaction.atomic():
            internship = Internship.objects.select_for_update().get(pk=internship_id)
            if hasattr(internship, 'certificate'):
                raise ValidationError('Certificate has already been generated.')
            if not internship.status:
                raise ValidationError('Internship details are required.')
            if internship.status != 'COMPLETED':
                internship.status = 'COMPLETED'
                internship.completed_at = timezone.now()
            if not internship.end_date:
                raise ValidationError('Please set the internship end date before generating the certificate.')
            data = snapshot(internship)
            if not all(data.values()) or data['gender'] not in ['MALE', 'FEMALE']:
                raise ValidationError('Complete student and internship details are required.')
            from accounts.serializers import StudentDetailsSerializer, student_data
            details = StudentDetailsSerializer(internship.student, data=student_data(internship.student))
            details.is_valid(raise_exception=True)
            today = timezone.localdate()
            sequence, _ = CertificateSequence.objects.get_or_create(year=today.year)
            sequence = CertificateSequence.objects.select_for_update().get(pk=sequence.pk)
            sequence.value += 1
            sequence.save(update_fields=['value'])
            cert = Certificate(internship=internship, certificate_id=f'INT-{today.year}-{sequence.value:05d}', issue_date=today, snapshot=data)
            url = f'{settings.FRONTEND_BASE_URL}/verify/{cert.verification_token}'
            payload = render_pdf(data, today, cert.certificate_id, url)
            cert.pdf_file.save(f'{cert.certificate_id}.pdf', ContentFile(payload), save=False)
            saved_file = cert.pdf_file
            cert.save()
            internship.status = 'CERTIFICATE_ISSUED'
            internship.save(update_fields=['status', 'updated_at'])
            return cert
    except Exception:
        if saved_file:
            saved_file.storage.delete(saved_file.name)
        raise
