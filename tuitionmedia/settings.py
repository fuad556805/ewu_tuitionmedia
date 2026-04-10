from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env file if exists
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ================= SECURITY =================
SECRET_KEY = os.getenv(
    'SECRET_KEY', 'django-insecure-tuitionmedia-secret-key-change-in-production'
)
DEBUG = os.getenv("DEBUG", "True") == "True"

# ================= ALLOWED HOSTS =================
if DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = os.getenv(
        "ALLOWED_HOSTS", "ewu-tuitionmedia.onrender.com"
    ).split(",")

# ================= CSRF TRUSTED ORIGINS =================
CSRF_TRUSTED_ORIGINS = [
    'https://*.replit.dev',
    'https://*.pike.replit.dev',
    'https://*.repl.co',
]
_extra_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if _extra_origins:
    CSRF_TRUSTED_ORIGINS += _extra_origins.split(",")

# ================= INSTALLED APPS =================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',

    # Custom apps
    'accounts',
    'posts',
    'tuitions',
    'chat',
    'guru',
    'admin_panel',
    'payments',
]

# ================= MIDDLEWARE =================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tuitionmedia.urls'
AUTH_USER_MODEL = 'accounts.User'

# ================= TEMPLATES =================
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
                'tuitionmedia.context_processors.vapid_key',
            ],
        },
    },
]

# ================= DATABASE =================
RENDER = os.getenv("RENDER", "FALSE").upper() == "TRUE"

if os.getenv('DATABASE_URL'):
    import urllib.parse
    _db_url = urllib.parse.urlparse(os.getenv('DATABASE_URL'))
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': _db_url.path[1:],
            'USER': _db_url.username,
            'PASSWORD': _db_url.password,
            'HOST': _db_url.hostname,
            'PORT': _db_url.port or '5432',
        }
    }
elif RENDER:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'mediaDB'),
            'USER': os.getenv('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'fuad1234@'),
            'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
        }
    }

# ================= STATIC & MEDIA =================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ================= AUTH =================
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ================= API KEYS =================
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
GEMINI_API_KEY    = os.getenv('GEMINI_API_KEY', '')
GEMINI_API_KEY_2  = os.getenv('GEMINI_API_KEY_2', '')
GROQ_API_KEY      = os.getenv('GROQ_API_KEY', '')
GROQ_API_KEY_2    = os.getenv('GROQ_API_KEY_2', '')

# ================= bKash =================
BKASH_BASE_URL   = os.getenv('BKASH_BASE_URL',   'https://tokenized.sandbox.bka.sh/v1.2.0-beta')
BKASH_APP_KEY    = os.getenv('BKASH_APP_KEY',    '')
BKASH_APP_SECRET = os.getenv('BKASH_APP_SECRET', '')
BKASH_USERNAME   = os.getenv('BKASH_USERNAME',   '')
BKASH_PASSWORD   = os.getenv('BKASH_PASSWORD',   '')

# ================= Nagad =================
NAGAD_BASE_URL      = os.getenv('NAGAD_BASE_URL',     'http://sandbox.mynagad.com:10080')
NAGAD_MERCHANT_ID   = os.getenv('NAGAD_MERCHANT_ID',  '')
NAGAD_MERCHANT_KEY  = os.getenv('NAGAD_MERCHANT_KEY', '')
NAGAD_PUBLIC_KEY    = os.getenv('NAGAD_PUBLIC_KEY',   '')

# ================= SMS =================
SMS_BACKEND   = os.getenv('SMS_BACKEND', 'console')   # console | stytch | twilio | bulksmsbd | sslwireless
SMS_FALLBACKS = os.getenv('SMS_FALLBACKS', 'bulksmsbd,console').split(',')

# Stytch
STYTCH_PROJECT_ID = os.getenv('STYTCH_PROJECT_ID', '')
STYTCH_SECRET     = os.getenv('STYTCH_SECRET', '')

# Twilio
TWILIO_ACCOUNT_SID        = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN         = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_FROM_NUMBER        = os.getenv('TWILIO_FROM_NUMBER', '')
TWILIO_VERIFY_SERVICE_SID = os.getenv('TWILIO_VERIFY_SERVICE_SID', '')

# BulkSMSBD (local BD)
BULKSMSBD_API_KEY   = os.getenv('BULKSMSBD_API_KEY', '')
BULKSMSBD_SENDER_ID = os.getenv('BULKSMSBD_SENDER_ID', '')

# SSL Wireless (local BD)
SSLWIRELESS_USERNAME = os.getenv('SSLWIRELESS_USERNAME', '')
SSLWIRELESS_PASSWORD = os.getenv('SSLWIRELESS_PASSWORD', '')
SSLWIRELESS_SID      = os.getenv('SSLWIRELESS_SID', '')

# ================= DRF =================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# ================= JWT =================
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS':  True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# ================= MESSAGE STORAGE =================
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# ================= WEB PUSH (VAPID) =================
VAPID_PUBLIC_KEY      = os.getenv('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY_B64 = os.getenv('VAPID_PRIVATE_KEY_B64', '')
VAPID_CLAIMS_EMAIL    = os.getenv('VAPID_CLAIMS_EMAIL', 'admin@tuitionmedia.com')

# ================= SECURITY HEADERS =================
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = False
