"""
Django settings for lizze_website project.

Notes:
 - This file expects environment variables (see comments below).
 - Required packages (ensure in requirements.txt):
    django
    gunicorn
    whitenoise
    python-decouple
    dj-database-url
    Pillow         # if you're using ImageField/FileField
"""

from pathlib import Path
import os
from decouple import config, Csv
import dj_database_url


# BASE_DIR = project root (two levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------
# SECURITY / ENV
# ---------------------------------------------------------------------
# Secret key (use a strong unique value in production — set DJANGO_SECRET_KEY)
# Default here is only for local development; DO NOT use in production.
SECRET_KEY = config('DJANGO_SECRET_KEY', default='unsafe-local-dev-secret')

# DEBUG: set DJANGO_DEBUG=True in your Render or local .env when developing
# DEBUG = config('DJANGO_DEBUG', default=False, cast=bool)
DEBUG = True

# Allowed hosts: comma-separated in env (e.g. "localhost,127.0.0.1,lashify-artistry.onrender.com")
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='127.0.0.1,localhost',
    cast=Csv()
)

# ---------------------------------------------------------------------
# APPLICATIONS / MIDDLEWARE
# ---------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Your app
    'Lashify_Artistry',

    # If you use sites framework
    'django.contrib.sites',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Whitenoise serves static files in production (after collectstatic)
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lizze_website.urls'

# ---------------------------------------------------------------------
# TEMPLATES
# ---------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # include both a project-level templates folder and your app's templates folder
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'Lashify_Artistry' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # required by admin and auth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lizze_website.wsgi.application'

# ---------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------
# Use DATABASE_URL envvar if set (Postgres on Render), otherwise fall back to sqlite
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'))
    )
}

# ---------------------------------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------
# INTERNATIONALIZATION
# ---------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------
# STATIC & MEDIA
# ---------------------------------------------------------------------
STATIC_URL = '/static/'

# Where Django will look for extra static files (the folder in your Lashify_Artistry app)
STATICFILES_DIRS = [
    BASE_DIR / 'Lashify_Artistry' / 'static',
]

# Where `collectstatic` will collect static files for production
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Whitenoise compressed manifest storage (recommended). If this causes issues,
# you can temporarily use 'whitenoise.storage.CompressedStaticFilesStorage'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Ensure the standard finders are enabled
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Media (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ---------------------------------------------------------------------
# DEFAULT PRIMARY KEY
# ---------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------
# EMAIL (Brevo / SMTP). Configure via env vars in Render or .env locally.
# ---------------------------------------------------------------------
# Example env variables to set:
# EMAIL_HOST (e.g. smtp-relay.brevo.com or provider's SMTP host)
# EMAIL_PORT (e.g. 587)
# EMAIL_USE_TLS (True/False)
# EMAIL_HOST_USER (your SMTP username or email)
# EMAIL_HOST_PASSWORD (your SMTP password or API key)
# DEFAULT_FROM_EMAIL (optional, fallback to EMAIL_HOST_USER)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp-relay.brevo.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER or 'webmaster@localhost')
BREVO_API_KEY = config("BREVO_API_KEY",default='')
ADMIN_EMAIL = "olamideadedokun36@gmail.com"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'booking_debug.log',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# ---------------------------------------------------------------------
# Optional security - turn on in production (configure as needed)
# ---------------------------------------------------------------------
if not DEBUG:
    # Make sure you have proper SSL termination & ALLOWED_HOSTS set when enabling:
    # SECURE_SSL_REDIRECT = True
    # SESSION_COOKIE_SECURE = True
    # CSRF_COOKIE_SECURE = True
    pass
