# -*- coding: utf-8 -*-
"""
Django settings for fieldnote_saas project.

Render（本番）とローカル開発の両方でそのまま動く “省略なしの完全版”。
- 静的ファイル: WhiteNoise（collectstatic 必須 / STATIC_ROOT 必須）
- DB: DATABASE_URL があればそれを使用、無ければ SQLite
- セキュリティ: SECRET_KEY/DEBUG は環境変数から
- i18n: 日本語、Asia/Tokyo
- カスタムユーザー: app.CustomUser
"""

from pathlib import Path
import os
import dj_database_url  # Render の PostgreSQL 接続用

# ==============================================================================
# 基本パス
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# セキュリティ
# ==============================================================================
# 本番では必ず環境変数で渡すこと。無い場合は開発用の値を使う（本番では絶対にこのデフォルト値を使わない）
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret-key-change-me")

# DEBUG は文字列 'true'/'false' を許可（既定 False）
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# 許可ホスト（Render の外部ホスト名を自動追加）
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# （任意）CSRF 許可オリジン: Render の URL（https://xxxx.onrender.com）を自動登録
# 環境変数に RENDER_EXTERNAL_URL を設定している場合のみ有効化
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
if RENDER_EXTERNAL_URL:
    from urllib.parse import urlparse

    parsed = urlparse(RENDER_EXTERNAL_URL)
    CSRF_TRUSTED_ORIGINS = [f"{parsed.scheme}://{parsed.netloc}"]
else:
    CSRF_TRUSTED_ORIGINS = []

# Proxy 経由の HTTPS 判定（Render 推奨）
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ==============================================================================
# アプリケーション
# ==============================================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",

    # 開発サーバでの static 衝突回避（django.contrib.staticfiles より前に）
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",

    # プロジェクトアプリ
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
        # プロジェクト直下に templates/ を置く場合は以下を有効化
        # "DIRS": [BASE_DIR / "templates"],
        "DIRS": [],
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

# ==============================================================================
# データベース
# ==============================================================================
# Render の Environment に DATABASE_URL（例: postgres://...）があればそれを使用
DATABASES = {}
if "DATABASE_URL" in os.environ:
    DATABASES["default"] = dj_database_url.config(
        conn_max_age=600,
        ssl_require=True,  # Render の Postgres は基本 SSL
    )
else:
    # ローカル開発用（SQLite）
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }

# ==============================================================================
# パスワードバリデータ
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==============================================================================
# 国際化 / タイムゾーン
# ==============================================================================
LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True          # ← タイポ注意（I18N）
USE_TZ = True

# ==============================================================================
# 静的/メディアファイル（WhiteNoise / collectstatic）
# ==============================================================================
# 推奨：先頭スラッシュ付き
STATIC_URL = "/static/"

# collectstatic の吐き先（必須）
STATIC_ROOT = BASE_DIR / "staticfiles"

# 任意：プロジェクト内に手動の静的ファイルを置く場合のみ有効化
# 例: BASE_DIR/static/... を参照させたいとき
# STATICFILES_DIRS = [BASE_DIR / "static"]

# ユーザーアップロード
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Django 5+ 推奨の STORAGES 形式
STORAGES = {
    # 既定ストレージ（アップロード用）。FileSystemStorage は storage 直下。
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": str(MEDIA_ROOT),
            "base_url": MEDIA_URL,
        },
    },
    # 静的ファイル（WhiteNoise：圧縮＋ハッシュ）
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ==============================================================================
# 既定設定
# ==============================================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# カスタムユーザーモデル
AUTH_USER_MODEL = "app.CustomUser"

# 認証関連
LOGIN_URL = "login"

# ==============================================================================
# メール（環境変数から読み込み）
# ==============================================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ==============================================================================
# （デプロイ時の自己診断：問題解決後に削除可）
# ==============================================================================
# collectstatic 失敗の再発を避けるためのワンショット検査
assert STATIC_ROOT, f"STATIC_ROOT is not set (loaded from {__name__})"
assert "staticfiles" in STORAGES, f"STORAGES['staticfiles'] missing (loaded from {__name__})"
# 最終確認 20251022