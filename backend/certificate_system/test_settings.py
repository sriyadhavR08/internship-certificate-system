import os
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-only-secret-not-for-deployment-000000000')
from .settings import *  # noqa
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'test-local.sqlite3'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
REST_FRAMEWORK = {**REST_FRAMEWORK, 'DEFAULT_THROTTLE_CLASSES': []}
