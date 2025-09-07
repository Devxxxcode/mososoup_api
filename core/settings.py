from pathlib import Path
from datetime import timedelta
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()


LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-dq+t^+uo*-k^=1)=c73$p%6103-hu#_d-fmie)0m=r$3n#qp=='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG',"true") == "true"

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'rest_framework_simplejwt.token_blacklist',
    'cloudinary_storage',
    'cloudinary',
    "corsheaders",


    # installed apps
    "users.apps.UsersConfig",
    "administration.apps.AdministrationConfig",
    "wallet.apps.WalletConfig",
    "packs.apps.PacksConfig",
    "finances.apps.FinancesConfig",
    "game.apps.GameConfig",
    "notification.apps.NotificationConfig",
]

MIDDLEWARE = [
    # 'users.middleware.SlowDownMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'users.middleware.UpdateLastConnectionMiddleware',
    'users.middleware.ConfigurableResetMiddleware',
    'shared.middleware.RequestLoggingMiddleware',
]

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = "US/Eastern"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


"---------------------------------------------Rest Framework Settings -------------------------------------------------"
REST_FRAMEWORK = {
    # Authentication settings: Use JWT for secure token-based authentication
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.middleware.CustomJWTAuthentication',
    ),

    # Pagination settings: Use a custom pagination class to format paginated responses
    # 'DEFAULT_PAGINATION_CLASS': 'shared.pagination.CustomPagination',

    # Default number of items per page in paginated results
    # 'PAGE_SIZE': 10,

    # Exception handling: Use a custom exception handler for consistent error responses
    'EXCEPTION_HANDLER': 'shared.exception_handler.custom_exception_handler',
}


"------------------------------- JSON Settings ------------------------------------------------------------------------"
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,

    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,

    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    "JTI_CLAIM": "jti",

    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),

    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}

"------------------------------------------------------ Logging Settings --------------------------------"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'custom_logger': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'cache_operations': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'request_logger': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'app.log'),
            'formatter': 'detailed',
        },
    },
    'formatters': {
        'simple': {
            'format': '%(levelname)s: %(message)s',
        },
        'detailed': {
            'format': '%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s',
        },
    },
}



"-------------------------------------- Postgres Settings --------------------------------"
use_postgres = os.getenv('USE_POSTGRES', '1') == '1'
if use_postgres:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DATABASE_NAME'),
            'USER': os.getenv('DATABASE_USER'),
            'PASSWORD': os.getenv('DATABASE_PASSWORD'),
            'HOST': os.getenv('DATABASE_HOST'),
            'PORT': os.getenv('DATABASE_PORT'),
        }
    }

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'adsterra_db',
#         'USER': 'postgres',
#         'PASSWORD': 'your_password',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'ads_api',  # Updated database name
#         'USER': 'mydb_owner',  # Updated user
#         'PASSWORD': 'jxKBk98pgmXa',  # Updated password
#         'HOST': 'ep-old-union-a5by6rze.us-east-2.aws.neon.tech',  # Updated host
#         'PORT': '5432',  # Same port
#     }
# }

# print(DATABASES["default"])


"------------------------------ Swagger Settings --------------------------------"
# swagger settings

SWAGGER_SETTINGS = {
   'SECURITY_DEFINITIONS': {
      'Basic': {
            'type': 'basic'
      },
      'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
      }
   }
}


"-------------------- Auth User ---------------------------------------"
AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend', 
    'core.backend.EmailOrUsernameBackend',
]


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

"---------------------------------------- CLOUDINARY_STORAGE -----------------------------------------------------"

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
    'RESOURCE_TYPE': 'video'
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'



"----------------------------------------------- CORS SETTINGS  -----------------------------------------------"

CORS_ALLOWS_ORIGINS = [
    "http://localhost:5500",
    "https://video-recording-api.onrender.com/videos/",
    "https://helpmeoo.netlify.app/",
    "https://malzahra.tech",
    "http://localhost:5173",
    "http://localhost:5173/",
]

CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

CORS_ALLOW_HEADERS = [
    "Accept",
    "Content-Type",
    "Authorization",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_ALL_ORIGINS = True

"----------------------------------------------- REDIS CACHE SETTINGS  -----------------------------------------------"

# Redis Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'ads_backend',
        'TIMEOUT': 7200,  # 2 hours default timeout
    }
}

# Cache TTL Settings (in seconds)
CACHE_TTL = {
    'PRODUCTS': 10800,  # 3 hours
    'PACKAGES': 10800,  # 3 hours
    'NOTIFICATIONS': 10800,  # 3 hours
    'SETTINGS': 14400,  # 4 hours
    'EVENTS': 14400,  # 4 hours
    'DEFAULT': 7200,  # 2 hours
}
