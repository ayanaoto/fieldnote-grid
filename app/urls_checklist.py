from django.urls import path
from . import views_checklist as v

urlpatterns = [
    # プロジェクト配下で新規チェックリストを作成
    path(
        "projects/<int:project_id>/checklists/create/",
        v.ChecklistCreateView.as_view(),
        name="checklist_create",
    ),

    # 既存チェックリストの編集
    path(
        "checklist/<int:pk>/edit/",
        v.ChecklistUpdateView.as_view(),
        name="checklist_edit",
    ),

    # チェックリストに項目（アイテム）を追加
    path(
        "checklist/<int:checklist_id>/items/add/",
        v.ChecklistItemCreateView.as_view(),
        name="checklist_item_add",
    ),
]
