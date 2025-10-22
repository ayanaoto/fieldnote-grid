# app/apps.py

from django.apps import AppConfig

class AppConfig(AppConfig): # ← このクラス名を使います
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'