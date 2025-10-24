# -*- coding: utf-8 -*-
"""
Django settings for fieldnote_saas project.
最終修正版（省略なし）
- Render とローカル両対応
- WhiteNoise + collectstatic（STATIC_ROOT 必須）
"""

from pathlib import Path
import os
import dj_database_url  # データベース接続のために追加

BASE_DIR = Path(__file__).resolve().parent.parent

# --- 1. セキュリティ設定 (重要) ---
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret-key-change-me")
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# --- 2. ALLOWED_HOSTS (Render 対応) ---
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Optional: RENDER_EXTERNAL_URL を設定しているなら CSRF_TRUSTED_ORIGINS を自動追加
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
if RENDER_EXTERNAL_URL:
    from urllib.parse import urlparse
    parsed = urlparse(RENDER_EXTERNAL_URL)
    CSRF_TRUSTED_ORIGINS = [f"{parsed.scheme}://{parsed.netloc}"]
else:
    CSRF_TRUSTED_ORIGINS = []

# --- Application definition ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",  # runserver と static の衝突回避
    "django.contrib.staticfiles",
    "app.apps.AppConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # SecurityMiddleware の直後
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
        "DIRS": [],  # 必要なら [BASE_DIR / "templates"]
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

# --- 3. データベース設定 (Render対応) ---
DATABASES = {}
if "DATABASE_URL" in os.environ:
    DATABASES["default"] = dj_database_url.config(conn_max_age=600, ssl_require=True)
else:
    DATABASES["default"] = {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True

# --- 4. 静的ファイル設定 (Render対応) ---
# 無条件で定義（インデントしないこと）
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# 任意: プロジェクト内に手動で置く static がある場合だけ有効化
# STATICFILES_DIRS = [BASE_DIR / "static"]

# メディア（ユーザーアップロード）
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Django 5+ 推奨の STORAGES 設定
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": str(MEDIA_ROOT), "base_url": MEDIA_URL},
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "app.CustomUser"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = '/'  # ログイン後に飛ぶ先をホームページに設定

# --- 5. メール送信設定 (セキュリティ対応) ---
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# === デバッグ用自己診断（成功したら削除してOK） ===
assert STATIC_ROOT, f"STATIC_ROOT is not set (loaded from {__name__})"
assert "staticfiles" in STORAGES, f"STORAGES['staticfiles'] missing (loaded from {__name__})"
