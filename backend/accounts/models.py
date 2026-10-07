from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('Email is required.')
        user = self.model(email=email.strip().lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.update(is_staff=True, is_superuser=True, role='ADMIN')
        return self.create_user(email, password, **extra)


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=120)
    role = models.CharField(max_length=10, choices=[('STUDENT', 'Student'), ('ADMIN', 'Admin')], default='STUDENT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    objects = UserManager()

    def __str__(self):
        return self.email


class StudentProfile(models.Model):
    CANDIDATE_TYPES = [
        ('SCHOOL_STUDENT', 'School Student Intern'),
        ('COLLEGE_INTERN', 'College Intern'),
        ('COLLEGE_COMPLETED', 'College Completed Student Intern'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    candidate_type = models.CharField(max_length=30, choices=CANDIDATE_TYPES, default='COLLEGE_INTERN')
    gender = models.CharField(max_length=6, choices=[('FEMALE', 'Female'), ('MALE', 'Male')])
    mobile_number = models.CharField(max_length=16)
    college_name = models.CharField(max_length=200)
    department = models.CharField(max_length=120)
    course = models.CharField(max_length=100)
    register_number = models.CharField(max_length=60, unique=True)
    college_id_card = models.FileField(upload_to='college_ids/', null=True, blank=True)
    selfie_photo = models.FileField(upload_to='selfies/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
