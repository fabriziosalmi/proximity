"""
Django settings for Proximity 2.0 project.

Built with security, scalability, and developer experience in mind.
"""

import os
from pathlib import Path
from datetime import timedelta
import dj_database_url

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'corsheaders',
    'ninja',
    
    # Proximity 2.0 apps
    'apps.core',
    'apps.proxmox',
    'apps.applications',
    'apps.catalog',
    'apps.backups',
    'apps.monitoring',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.SentryUserContextMiddleware',  # Sentry user context enrichment
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'proximity.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'proximity.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL)
}

# Custom User Model
AUTH_USER_MODEL = 'core.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Configuration
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS', 
    'http://localhost:5173'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_LIFETIME = timedelta(minutes=60)
JWT_REFRESH_TOKEN_LIFETIME = timedelta(days=7)

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Redis Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Channels Configuration (for WebSockets)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

# Proxmox Configuration
PROXMOX_HOST = os.getenv('PROXMOX_HOST', '')
PROXMOX_USER = os.getenv('PROXMOX_USER', 'root@pam')
PROXMOX_PASSWORD = os.getenv('PROXMOX_PASSWORD', '')
PROXMOX_VERIFY_SSL = os.getenv('PROXMOX_VERIFY_SSL', 'False') == 'True'
PROXMOX_PORT = int(os.getenv('PROXMOX_PORT', '8006'))

# Sentry Configuration
SENTRY_DSN = os.getenv('SENTRY_DSN', None)
SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', 'development')
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '1.0'))
SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1'))

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    def before_send_transaction(event, hint):
        """Filter out noise from transactions to reduce quota usage."""
        url = event.get('request', {}).get('url', '')
        transaction_name = event.get('transaction', '')
        
        # Skip health checks and monitoring endpoints
        if '/health' in url or '/api/health' in transaction_name:
            return None
        if '/metrics' in url or '/prometheus' in url:
            return None
        
        # Skip static file requests
        if '/static/' in url or '/media/' in url:
            return None
            
        return event

    def before_send(event, hint):
        """Filter events to reduce noise and quota usage."""
        # Don't send events in DEBUG mode unless explicitly configured
        if DEBUG and os.getenv('SENTRY_DEBUG', 'False') != 'True':
            return None
        
        # Skip certain logger names that are too noisy
        if event.get('logger') in ['django.server', 'django.request']:
            # Only send errors, not info/debug from these loggers
            if event.get('level') not in ['error', 'fatal']:
                return None
        
        return event

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                transaction_style='url',  # Use URL pattern for transaction names
                middleware_spans=False,   # Reduce span noise
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,
                exclude_beat_tasks=None,
            ),
            RedisIntegration(),
        ],
        environment=SENTRY_ENVIRONMENT,
        release=os.getenv('SENTRY_RELEASE', 'proximity@2.0.0'),
        
        # Sampling rates - reduce to avoid quota limits
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,
        
        # Event filtering
        before_send=before_send,
        before_send_transaction=before_send_transaction,
        
        # Performance options
        send_default_pii=True,
        attach_stacktrace=True,
        max_breadcrumbs=50,  # Limit breadcrumbs to reduce payload size
        
        # Reduce background overhead
        shutdown_timeout=2,  # Faster shutdown
        transport_queue_size=30,  # Smaller queue to reduce memory
    )

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}


# ======================================================================
# CATALOG SETTINGS
# ======================================================================

# Path to catalog data directory containing application JSON files
CATALOG_DATA_PATH = BASE_DIR.parent / 'catalog_data'


# ======================================================================
# TESTING SETTINGS
# ======================================================================

# Enable testing mode to bypass Proxmox connections and simulate deployments
TESTING_MODE = os.getenv('TESTING_MODE', 'False') == 'True'
