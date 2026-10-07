from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from accounts import views as a
from certificates import views as c

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/register/', a.register), path('api/auth/login/', a.LoginView.as_view()),
    path('api/auth/token/refresh/', TokenRefreshView.as_view()), path('api/auth/logout/', a.logout), path('api/auth/me/', a.me),
    path('api/student/profile/', a.profile), path('api/student/internship/', a.profile), path('api/student/certificate/', a.my_certificate),
    path('api/admin/dashboard/', a.dashboard), path('api/admin/students/', a.students),
    path('api/admin/students/<int:pk>/', a.student_detail), path('api/admin/internships/<int:pk>/status/', a.status),
    path('api/admin/internships/<int:pk>/end-date/', a.set_end_date),
    path('api/admin/certificates/', c.certificates), path('api/admin/certificates/preview/<int:pk>/', c.preview),
    path('api/admin/certificates/generate/<int:pk>/', c.issue), path('api/admin/certificates/<int:pk>/revoke/', c.revoke),
    path('api/certificates/<int:pk>/download/', c.download),
    path('api/public/captcha/', c.get_captcha),
    path('api/public/verify/token/<str:token>/', c.verify), path('api/public/verify/id/<str:certificate_id>/', c.verify),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

