import os
from pathlib import Path
from google.cloud import secretmanager
from decouple import config 

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Function to get secrets from Google Secret Manager
def get_secret(secret_id, project_id="easydealsapp"):
    """Get secret from Google Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception:
        # Fallback for local development
        return os.environ.get(secret_id, '')

# Detect if running on Cloud Run
IS_CLOUD_RUN = os.getenv('GAE_APPLICATION', None) or os.getenv('GOOGLE_CLOUD_PROJECT', None)

if IS_CLOUD_RUN:
    # Production settings
    SECRET_KEY = get_secret("django-secret-key")
    DEBUG = False
    
    # Database configuration for Cloud Run
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'HOST': f'/cloudsql/{get_secret("cloud-sql-connection")}',
            'USER': get_secret("db-user"),
            'PASSWORD': get_secret("db-password"),
            'NAME': get_secret("db-name"),
        }
    }
    
else:
    # Local development settings
    SECRET_KEY = 'django-insecure-local-development-key'
    DEBUG = True
    
    # Local SQLite database
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Cloud Run provides the PORT environment variable
PORT = int(os.environ.get('PORT', 8080))

ALLOWED_HOSTS = ['*']  # Cloud Run handles this

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_filters',
    'storages',

    # Local apps
    'apps.users.apps.UsersConfig',
    'apps.businesses.apps.BusinessesConfig',
    'apps.orders.apps.OrdersConfig',
    'apps.authentication.apps.AuthenticationConfig',
    'apps.payments.apps.PaymentsConfig',
    'apps.notifications.apps.NotificationsConfig',
    'apps.tracking.apps.TrackingConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'easydeals_backend.urls'

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

WSGI_APPLICATION = 'easydeals_backend.wsgi.application'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# CORS
CORS_ALLOW_ALL_ORIGINS = True  

# Internationalization
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Panama'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Tilopay Configuration (usando os.environ)
TILOPAY_BASE_URL = os.environ.get('TILOPAY_BASE_URL', 'https://api.tilopay.com')
TILOPAY_API_KEY = os.environ.get('TILOPAY_API_KEY', '')
TILOPAY_SECRET_KEY = os.environ.get('TILOPAY_SECRET_KEY', '')
TILOPAY_PLATFORM_KEY = os.environ.get('TILOPAY_PLATFORM_KEY', '')
TILOPAY_PLATFORM_SUBMERCHANT_KEY = os.environ.get('TILOPAY_PLATFORM_SUBMERCHANT_KEY', '')

# URLs for redirects
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
BACKEND_URL = os.environ.get('BACKEND_URL', 'https://easydeals-backend-6b3hktb2rq-uc.a.run.app')