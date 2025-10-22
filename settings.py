"""
Django settings for fieldnote_saas project.
"""
from pathlib import Path
import os
import dj_database_url  # RenderのPostgreSQL接続

# ------------------------------------------------------------------------------
# 基本パス
# ------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------------------
# セキュリティ
# ------------------------------------------------------------------------------
# 本番は必ず環境変数で渡す
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret-key-change-me")

DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# Renderのドメインを自動許可
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# （必要に応じて）CSRF許可：Renderの *.onrender.com を許可
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")  # 例: https://xxxx.onrender.com
if RENDER_EXTERNAL_URL:
    # 形式は https://host のみ（パスなし）
    from urllib.parse import urlparse
    host = urlparse(RENDER_EXTERNAL_URL).scheme + "://" + urlparse(RENDER_EXTERNAL_URL).netloc
    CSRF_TRUSTED_ORIGINS = [host]
else:
    CSRF_TRUSTED_ORIGINS = []

# ------------------------------------------------------------------------------
# アプリ
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # 開発中 runserver での static 衝突回避（推奨）
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "app.apps.AppConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise は SecurityMiddleware の直後
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "fieldnote_saas.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # プロジェクト直下 templates/ を使うなら [BASE_DIR / "templates"]
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "fieldnote_saas.wsgi.application"

# ------------------------------------------------------------------------------
# データベース（Render は DATABASE_URL 使用）
# ------------------------------------------------------------------------------
DATABASES = {}
if "DATABASE_URL" in os.environ:
    DATABASES["default"] = dj_database_url.config(
        conn_max_age=600,
        ssl_require=True,
    )
else:
    # ローカル開発用
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }

# ------------------------------------------------------------------------------
# パスワードバリデータ
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------------------
# 国際化
# ------------------------------------------------------------------------------
LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
# ← 元の設定にタイポがありました（USE_I1N）。正しくは USE_I18N。
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------------------
# 静的/メディア ファイル（Render/WhiteNoise対応）
# ------------------------------------------------------------------------------
# URL は先頭スラッシュ付きが推奨
STATIC_URL = "/static/"
# collectstatic の吐き先（必須）
STATIC_ROOT = BASE_DIR / "staticfiles"

# プロジェクト内に手動配置した静的ファイルがある場合だけ有効化
# 例: BASE_DIR/static/... を使うならコメント解除
# STATICFILES_DIRS = [BASE_DIR / "static"]

# ユーザーアップロード
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Django 5 以降推奨の STORAGES 方式
STORAGES = {
    # 既定ストレージ（アップロード用）。FileSystemStorage は storage モジュール直下です。
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": str(MEDIA_ROOT),
            "base_url": MEDIA_URL,
        },
    },
    # 静的ファイル（WhiteNoise の圧縮＋ハッシュ）
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ------------------------------------------------------------------------------
# その他
# ------------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "app.CustomUser"
LOGIN_URL = "login"

# ------------------------------------------------------------------------------
# メール（環境変数から）
# ------------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
