from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # アプリ本体
    path("", include("app.urls")),

    # チェックリスト用のURL（本回答で追加したファイル）
    path("", include("app.urls_checklist")),
]

# 任意：カスタムエラーハンドラを使っていないなら何も書かなくてOK
# handler404 = "app.views.handler404"
# handler500 = "app.views.handler500"
