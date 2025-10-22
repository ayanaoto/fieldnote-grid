"""
Django settings for fieldnote_saas project.
"""

from pathlib import Path
import os
import dj_database_url # データベース接続のために追加

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# --- 1. セキュリティ設定 (重要) ---
# SECRET_KEYは環境変数から読み込みます。
SECRET_KEY = os.environ.get('SECRET_KEY')

# DEBUGモードは環境変数から読み込みます。
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# --- 2. ALLOWED_HOSTS (500エラーの修正) ---
# Renderのドメインを自動で許可リストに追加します。
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # Whitenoise (静的ファイル配信用) を追加
    'django.contrib.staticfiles',
    'app.apps.AppConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Whitenoise (静的ファイル配信用) を追加
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fieldnote_saas.urls'

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

WSGI_APPLICATION = 'fieldnote_saas.wsgi.application'


# --- 3. データベース設定 (Render対応) ---
# Renderの 'Environment' で設定した 'DATABASE_URL' を自動で読み込みます。
DATABASES = {}
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        ssl_require=True # RenderのPostgreSQLはSSL接続が必須です
    )
else:
    # ローカル開発用の設定
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# Internationalization
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I1N = True
USE_TZ = True


# --- 4. 静的ファイル設定 (Render対応) ---
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
# 'collectstatic' で集められる静的ファイルの置き場所
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# 修正点：
# 以前の STATICFILES_STORAGE の代わりに、
# 新しい STORAGES 辞書を使うように変更しました。
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.filesystem.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'app.CustomUser'
LOGIN_URL = 'login'

# --- 5. メール送信設定 (セキュリティ対応) ---
# メール設定も環境変数から読み込みます
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

