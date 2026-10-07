from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .models import User
from .permissions import IsAdmin, IsStudent
from .serializers import RegisterSerializer, StudentDetailsSerializer, LoginSerializer, student_data, certificate_data
from internships.models import Internship
from certificates.models import Certificate


class AuthThrottle(AnonRateThrottle):
    scope = 'auth'


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    throttle_classes = [AuthThrottle]


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({'success': True, 'message': 'Registration successful. Please sign in.'}, status=201)


@api_view(['GET'])
def me(request):
    u = request.user
    return Response({'id': u.pk, 'full_name': u.full_name, 'email': u.email, 'role': u.role})


@api_view(['POST'])
def logout(request):
    try:
        token = RefreshToken(request.data.get('refresh', ''))
    except TokenError as exc:
        raise InvalidToken(str(exc))
    if str(token['user_id']) != str(request.user.pk):
        raise ValidationError('Invalid refresh token.')
    token.blacklist()
    return Response({'message': 'Signed out.'})


@api_view(['GET'])
@permission_classes([IsStudent])
def profile(request):
    return Response(student_data(request.user))


@api_view(['GET'])
@permission_classes([IsStudent])
def my_certificate(request):
    return Response(certificate_data(getattr(request.user.internship, 'certificate', None)))


def students_query():
    return User.objects.filter(role='STUDENT').select_related('profile', 'internship', 'internship__certificate').order_by('-created_at')


@api_view(['GET'])
@permission_classes([IsAdmin])
def students(request):
    query = students_query()
    search = request.query_params.get('search', '')
    if search:
        query = query.filter(Q(full_name__icontains=search) | Q(email__icontains=search) | Q(profile__register_number__icontains=search))
    for key in ['status', 'project_name', 'start_date', 'end_date']:
        value = request.query_params.get(key)
        if value:
            if key.endswith('_date'):
                from datetime import date
                try:
                    date.fromisoformat(value)
                except ValueError:
                    raise ValidationError({key: 'Use YYYY-MM-DD.'})
            query = query.filter(**{f'internship__{key}': value})
    try:
        page = max(1, int(request.query_params.get('page', 1)))
    except ValueError:
        raise ValidationError('Invalid page.')
    total = query.count()
    return Response({'count': total, 'page': page, 'results': [student_data(u) for u in query[(page-1)*20:page*20]]})


@api_view(['GET', 'PUT'])
@permission_classes([IsAdmin])
def student_detail(request, pk):
    with transaction.atomic():
        user = get_object_or_404(User, pk=pk, role='STUDENT')
        internship = Internship.objects.select_for_update().get(student=user)
        if request.method == 'PUT':
            if hasattr(internship, 'certificate'):
                raise ValidationError('Issued certificate details are immutable. Revoke the certificate if it is incorrect.')
            serializer = StudentDetailsSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(student_data(User.objects.get(pk=pk)))


@api_view(['PATCH'])
@permission_classes([IsAdmin])
def status(request, pk):
    with transaction.atomic():
        internship = get_object_or_404(Internship.objects.select_for_update(), pk=pk)
        target = request.data.get('status')
        if target not in ['REGISTERED', 'IN_PROGRESS', 'COMPLETED']:
            raise ValidationError('Invalid status target.')
        internship.status = target
        if target == 'COMPLETED':
            internship.completed_at = timezone.now()
        internship.save()
        return Response(student_data(internship.student))


@api_view(['PATCH', 'POST'])
@permission_classes([IsAdmin])
def set_end_date(request, pk):
    with transaction.atomic():
        internship = get_object_or_404(Internship.objects.select_for_update(), pk=pk)
        end_date_str = request.data.get('end_date')
        if not end_date_str:
            raise ValidationError({'end_date': 'End date is required.'})
        from datetime import date
        try:
            d = date.fromisoformat(end_date_str)
        except ValueError:
            raise ValidationError({'end_date': 'Invalid date format (YYYY-MM-DD).'})
        if internship.start_date and d <= internship.start_date:
            raise ValidationError({'end_date': 'End date must be after start date.'})
        internship.end_date = d
        internship.save(update_fields=['end_date', 'updated_at'])
        return Response(student_data(internship.student))


@api_view(['GET'])
@permission_classes([IsAdmin])
def dashboard(request):
    return Response({'counts': {'Total students': User.objects.filter(role='STUDENT').count(),
        'Active internships': Internship.objects.filter(status='IN_PROGRESS').count(),
        'Completed internships': Internship.objects.filter(status__in=['COMPLETED', 'CERTIFICATE_ISSUED']).count(),
        'Certificates issued': Certificate.objects.count()},
        'recent_students': [student_data(u) for u in students_query()[:5]],
        'recent_certificates': [certificate_data(c) for c in Certificate.objects.order_by('-created_at')[:5]]})
