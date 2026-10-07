import base64
import uuid
from datetime import timedelta
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, StudentProfile
from internships.models import Internship


def save_base64_file(data_uri, prefix='file'):
    if not data_uri:
        return None
    if hasattr(data_uri, 'read'):
        return data_uri
    if not isinstance(data_uri, str) or not data_uri.startswith('data:'):
        return None
    try:
        header, encoded = data_uri.split(';base64,', 1)
        mime = header.split(':', 1)[-1].split(';')[0].lower()
        ext = mime.split('/')[-1] if '/' in mime else 'jpg'
        if ext in ['jpeg', 'jpg']:
            ext = 'jpg'
        elif ext == 'png':
            ext = 'png'
        elif ext == 'webp':
            ext = 'webp'
        elif ext == 'pdf':
            ext = 'pdf'
        else:
            ext = 'jpg'
        decoded = base64.b64decode(encoded)
        filename = f"{prefix}_{uuid.uuid4().hex[:10]}.{ext}"
        return ContentFile(decoded, name=filename)
    except Exception:
        return None



class StudentDetailsSerializer(serializers.Serializer):
    candidate_type = serializers.ChoiceField(choices=['SCHOOL_STUDENT', 'COLLEGE_INTERN', 'COLLEGE_COMPLETED'], required=False, default='COLLEGE_INTERN')
    full_name = serializers.CharField(max_length=120)
    email = serializers.EmailField()
    gender = serializers.ChoiceField(choices=['FEMALE', 'MALE'])
    mobile_number = serializers.RegexField(r'^\+?[0-9]{10,15}$', max_length=16)
    college_name = serializers.CharField(max_length=200)
    department = serializers.CharField(max_length=120)
    course = serializers.CharField(max_length=100)
    register_number = serializers.CharField(max_length=60)
    project_name = serializers.CharField(max_length=150)
    start_date = serializers.DateField()
    end_date = serializers.DateField(required=False, allow_null=True)
    college_id_card = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    selfie_photo = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_email(self, value):
        value = value.strip().lower()
        existing = User.objects.filter(email__iexact=value)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError('Email already registered.')
        return value

    def validate_register_number(self, value):
        value = value.strip().upper()
        existing = StudentProfile.objects.filter(register_number__iexact=value)
        if self.instance:
            existing = existing.exclude(user=self.instance)
        if existing.exists():
            raise serializers.ValidationError('Register number already exists.')
        return value

    def validate(self, data):
        start = data.get('start_date')
        end = data.get('end_date')
        if end and start and end <= start:
            raise serializers.ValidationError({'end_date': 'End date must be after start date.'})
        for key in ['full_name', 'project_name']:
            if key in data and any(ord(c) < 32 for c in data[key]):
                raise serializers.ValidationError({key: 'Control characters are not allowed.'})
        return data

    def update(self, instance, data):
        instance.full_name = data.pop('full_name')
        instance.email = data.pop('email')
        instance.save()
        internship = instance.internship
        for key in ['project_name', 'start_date', 'end_date']:
            if key in data:
                setattr(internship, key, data.pop(key))
        internship.save()
        profile = instance.profile
        college_id_card = data.pop('college_id_card', None)
        selfie_photo = data.pop('selfie_photo', None)
        if college_id_card:
            file_obj = save_base64_file(college_id_card, 'college_id')
            if file_obj:
                profile.college_id_card = file_obj
        if selfie_photo:
            file_obj = save_base64_file(selfie_photo, 'selfie')
            if file_obj:
                profile.selfie_photo = file_obj
        for key, value in data.items():
            setattr(profile, key, value)
        profile.save()
        return instance


class RegisterSerializer(StudentDetailsSerializer):
    password = serializers.CharField(write_only=True, max_length=128)
    confirm_password = serializers.CharField(write_only=True, max_length=128)

    def validate(self, data):
        data = super().validate(data)
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        try:
            validate_password(data['password'], User(email=data['email'], full_name=data['full_name']))
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': exc.messages})
        return data

    @transaction.atomic
    def create(self, data):
        data.pop('confirm_password')
        candidate_type = data.pop('candidate_type', 'COLLEGE_INTERN')
        college_id_card_raw = data.pop('college_id_card', None)
        selfie_photo_raw = data.pop('selfie_photo', None)
        end_date = data.pop('end_date', None)
        user = User.objects.create_user(email=data.pop('email'), full_name=data.pop('full_name'), password=data.pop('password'))
        Internship.objects.create(
            student=user,
            project_name=data.pop('project_name'),
            start_date=data.pop('start_date'),
            end_date=end_date
        )
        profile = StudentProfile.objects.create(user=user, candidate_type=candidate_type, **data)
        if college_id_card_raw:
            file_obj = save_base64_file(college_id_card_raw, 'college_id')
            if file_obj:
                profile.college_id_card = file_obj
        if selfie_photo_raw:
            file_obj = save_base64_file(selfie_photo_raw, 'selfie')
            if file_obj:
                profile.selfie_photo = file_obj
        profile.save()
        return user


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        attrs['email'] = attrs.get('email', '').strip().lower()
        data = super().validate(attrs)
        data['user'] = {'id': self.user.pk, 'full_name': self.user.full_name, 'email': self.user.email, 'role': self.user.role}
        return data


def certificate_data(cert):
    if not cert:
        return None
    return {'id': cert.pk, 'certificate_id': cert.certificate_id, 'issue_date': cert.issue_date,
            'status': cert.status, 'verification_url': f'/verify/{cert.verification_token}',
            'student_name': cert.snapshot.get('student_name'), 'project_name': cert.snapshot.get('project_name')}


def student_data(user):
    p = getattr(user, 'profile', None)
    i = getattr(user, 'internship', None)
    if not p or not i:
        return {'id': user.pk, 'full_name': user.full_name, 'email': user.email}

    college_id_url = None
    if getattr(p, 'college_id_card', None) and bool(p.college_id_card):
        try:
            url = p.college_id_card.url
            college_id_url = f"http://127.0.0.1:8001{url}" if url.startswith('/') else url
        except Exception:
            college_id_url = None

    selfie_url = None
    if getattr(p, 'selfie_photo', None) and bool(p.selfie_photo):
        try:
            url = p.selfie_photo.url
            selfie_url = f"http://127.0.0.1:8001{url}" if url.startswith('/') else url
        except Exception:
            selfie_url = None

    duration = (i.end_date - i.start_date).days + 1 if (i.end_date and i.start_date) else None
    cand_type = getattr(p, 'candidate_type', 'COLLEGE_INTERN')
    cand_label_map = {
        'SCHOOL_STUDENT': 'School Student Intern',
        'COLLEGE_INTERN': 'College Intern',
        'COLLEGE_COMPLETED': 'College Completed Student Intern'
    }
    return {
        'id': user.pk,
        'full_name': user.full_name,
        'email': user.email,
        'candidate_type': cand_type,
        'candidate_type_display': cand_label_map.get(cand_type, 'College Intern'),
        **{k: getattr(p, k, '') for k in ['gender', 'mobile_number', 'college_name', 'department', 'course', 'register_number']},
        'college_id_card': college_id_url,
        'selfie_photo': selfie_url,
        'internship_id': i.pk,
        **{k: getattr(i, k, None) for k in ['project_name', 'start_date', 'end_date', 'status', 'completed_at']},
        'duration_days': duration,
        'certificate': certificate_data(getattr(i, 'certificate', None))
    }

