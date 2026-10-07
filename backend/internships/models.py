from django.db import models
from django.conf import settings


class Internship(models.Model):
    STATUSES = [(s, s.replace('_', ' ').title()) for s in ['REGISTERED', 'IN_PROGRESS', 'COMPLETED', 'CERTIFICATE_ISSUED']]
    student = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='internship')
    project_name = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='REGISTERED')
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(end_date__isnull=True) | models.Q(end_date__gt=models.F('start_date')), name='internship_dates_ordered')]
