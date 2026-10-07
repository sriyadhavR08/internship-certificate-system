import secrets
from django.db import models


def secure_token():
    return secrets.token_urlsafe(32)


class CertificateSequence(models.Model):
    year = models.PositiveIntegerField(primary_key=True)
    value = models.PositiveIntegerField(default=0)


class Certificate(models.Model):
    internship = models.OneToOneField('internships.Internship', on_delete=models.PROTECT, related_name='certificate')
    certificate_id = models.CharField(max_length=30, unique=True)
    verification_token = models.CharField(max_length=64, unique=True, default=secure_token, editable=False)
    issue_date = models.DateField()
    pdf_file = models.FileField(upload_to='certificates/', blank=True)
    snapshot = models.JSONField(default=dict)
    status = models.CharField(max_length=10, choices=[('VALID', 'Valid'), ('REVOKED', 'Revoked')], default='VALID')
    generated_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
