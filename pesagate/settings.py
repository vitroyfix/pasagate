"""
Django settings for pesagate project.
"""

from pathlib import Path
from decouple import config
import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

# Used later when building the STK callback URL Safaricom sends results to.
PUBLIC_BASE_URL = config("PUBLIC_BASE_URL", default="http://localhost:8000")


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'accounts',
    'vault',
    'stk',
    'billing',
]

# Tells Django to use OUR custom User model (built in Step 5) instead of
# the built-in one. Must be set before the first migration ever runs —
# changing it afterward requires resetting the whole database.
AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pesagate.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pesagate.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
# Defaults to SQLite if DB_ENGINE isn't set in .env — switch to Postgres
# later purely by editing .env, no code change needed.

DATABASES = {
    'default': {
        'ENGINE': config("DB_ENGINE", default="django.db.backends.sqlite3"),
        'NAME': config("DB_NAME", default=BASE_DIR / 'db.sqlite3'),
        'USER': config("DB_USER", default=""),
        'PASSWORD': config("DB_PASSWORD", default=""),
        'HOST': config("DB_HOST", default=""),
        'PORT': config("DB_PORT", default=""),
    }
}


# Cache — backed by Redis. Used to cache the Daraja OAuth access token
# (valid ~1hr) so we're not re-authenticating with Safaricom on every
# single STK push. Requires Redis actually running before any code
# calls cache.get()/cache.set() — install with `sudo dnf install redis`
# and start with `sudo systemctl start redis`.

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config("REDIS_URL", default="redis://localhost:6379/0"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework — every API view defaults to requiring a valid
# JWT unless a view explicitly overrides permission_classes (like the
# Safaricom callback endpoint will, since Safaricom can't send a JWT).

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# How long a login stays valid before needing to re-authenticate.
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=7),
}


# Celery — background job queue. Used later for B2C payouts (Track 2)
# so a Safaricom callback response doesn't block on a slow payout call.
# Reuses the same Redis instance as CACHES above, just as the message broker.

CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}