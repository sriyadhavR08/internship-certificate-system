from django.db import transaction
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from accounts.permissions import IsAdmin
from accounts.serializers import certificate_data
from internships.models import Internship
from .models import Certificate
from .content import snapshot
from .layout import render_pdf
from .services import generate


@api_view(['GET'])
@permission_classes([IsAdmin])
def preview(request, pk):
    internship = get_object_or_404(Internship, pk=pk)
    response = HttpResponse(render_pdf(snapshot(internship), timezone.localdate()), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="certificate-preview.pdf"'
    response['Cache-Control'] = 'no-store'
    return response


@api_view(['POST'])
@permission_classes([IsAdmin])
def issue(request, pk):
    get_object_or_404(Internship, pk=pk)
    cert = generate(pk)
    return Response(certificate_data(cert), status=201)


@api_view(['GET'])
@permission_classes([IsAdmin])
def certificates(request):
    query = Certificate.objects.order_by('-created_at')
    search = request.query_params.get('search', '')
    if search:
        query = query.filter(certificate_id__icontains=search)
    status = request.query_params.get('status')
    if status:
        query = query.filter(status=status)
    try:
        page = max(1, int(request.query_params.get('page', 1)))
    except ValueError:
        raise ValidationError('Invalid page.')
    return Response({'count': query.count(), 'page': page, 'results': [certificate_data(c) for c in query[(page-1)*20:page*20]]})


@api_view(['PATCH'])
@permission_classes([IsAdmin])
def revoke(request, pk):
    with transaction.atomic():
        cert = get_object_or_404(Certificate.objects.select_for_update(), pk=pk)
        if cert.status != 'REVOKED':
            cert.status = 'REVOKED'
            cert.revoked_at = timezone.now()
            cert.save(update_fields=['status', 'revoked_at', 'updated_at'])
        return Response(certificate_data(cert))


@api_view(['GET'])
def download(request, pk):
    cert = get_object_or_404(Certificate.objects.select_related('internship'), pk=pk)
    if request.user.role != 'ADMIN' and cert.internship.student_id != request.user.pk:
        raise PermissionDenied('You can only access your own certificate.')
    if cert.status == 'REVOKED':
        raise PermissionDenied('This certificate has been revoked.')
    response = FileResponse(cert.pdf_file.open('rb'), as_attachment=True, filename=f'{cert.certificate_id}.pdf', content_type='application/pdf')
    response['Cache-Control'] = 'no-store'
    return response


import random
import hmac
import hashlib
import time
from django.conf import settings


def make_captcha():
    # 6-digit security OTP verification code
    otp = f"{random.randint(100000, 999999)}"
    exp = int(time.time()) + 600
    raw = f"{otp}:{exp}"
    sig = hmac.new(settings.SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()
    token = f"{otp}:{exp}:{sig}"
    return {
        'otp': otp,
        'code': otp,
        'question': otp,
        'token': token,
        'expires_in': 600
    }


def validate_captcha(token, user_answer):
    if not token or user_answer is None:
        return False
    try:
        parts = str(token).split(':')
        if len(parts) != 3:
            return False
        expected_ans, exp_str, sig = parts
        if time.time() > int(exp_str):
            return False
        raw = f"{expected_ans}:{exp_str}"
        valid_sig = hmac.new(settings.SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, valid_sig):
            return False
        clean_user = str(user_answer).replace(' ', '').replace('-', '').strip()
        clean_expected = str(expected_ans).replace(' ', '').replace('-', '').strip()
        return clean_user == clean_expected
    except Exception:
        return False


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def get_captcha(request):
    return Response(make_captcha())


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def verify(request, token=None, certificate_id=None):
    captcha_token = request.data.get('captcha_token') if request.method == 'POST' else request.query_params.get('captcha_token')
    captcha_answer = request.data.get('captcha_answer') if request.method == 'POST' else request.query_params.get('captcha_answer')

    if not validate_captcha(captcha_token, captcha_answer):
        raise ValidationError({'captcha': 'Security verification failed. Please enter the valid 6-digit OTP code.'})


    lookup = {'verification_token': token} if token else {'certificate_id': certificate_id.upper()}
    cert = get_object_or_404(Certificate.objects.select_related('internship__student__profile'), **lookup)
    profile = getattr(cert.internship.student, 'profile', None)
    cand_type = getattr(profile, 'candidate_type', 'COLLEGE_INTERN') if profile else cert.snapshot.get('candidate_type', 'COLLEGE_INTERN')
    cand_label_map = {
        'SCHOOL_STUDENT': 'School Student Intern',
        'COLLEGE_INTERN': 'College Intern',
        'COLLEGE_COMPLETED': 'College Completed Student Intern'
    }
    result = {
        'student_name': cert.snapshot.get('student_name', cert.internship.student.full_name),
        'candidate_type': cand_type,
        'candidate_type_label': cand_label_map.get(cand_type, 'College Intern'),
        'certificate_id': cert.certificate_id,
        'status': cert.status,
        'verified_status': 'Certified Verified' if cert.status == 'VALID' else 'Certificate Revoked',
        'college_name': profile.college_name if profile else cert.snapshot.get('institution_name', ''),
        'department': profile.department if profile else cert.snapshot.get('department', ''),
        'course': profile.course if profile else cert.snapshot.get('course', ''),
        'register_number': profile.register_number if profile else cert.snapshot.get('register_number', ''),
        'verified_at': timezone.now().strftime('%d %B %Y, %I:%M %p')
    }
    if cert.status == 'VALID':
        result.update({key: cert.snapshot.get(key) for key in ['project_name', 'start_date', 'end_date']})
        result['issue_date'] = cert.issue_date
    return Response(result)
