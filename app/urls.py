# app/urls.py

from django.urls import path

from .views import (
    # 認証/ホーム
    SignUpView,
    CustomLoginView,
    CustomLogoutView,
    HomeView,
    HowToUseView, # ★ 追加

    # プロジェクト
    ProjectListView,
    ProjectCreateView,
    ProjectDetailView,
    ProjectUpdateView,
    ProjectDeleteView,
    ProjectPDFView,
    GanttPDFView,

    # メンバー管理/招待
    MemberManagementView,
    AcceptInvitationView,
    MemberDeleteView,
    InvitationDeleteView,

    # ガント/タスク JSON
    ProjectTaskJSONView,
)

# 共有メモは分割ファイルから
from .views_memo import MemoCreateView, MemoUpdateView

# チェックリストは分割ファイルから
from .views_checklist import (
    ChecklistCreateView,
    ChecklistUpdateView,
    ChecklistItemCreateView,
    ChecklistItemUpdateView,
    ChecklistItemToggleView,
)

# タスクは分割ファイルから
from .views_task import TaskCreateView, TaskUpdateView, TaskDeleteView


urlpatterns = [
    # 認証/トップ
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("", HomeView.as_view(), name="home"),
    
    # ★ この行を追加
    path("how-to-use/", HowToUseView.as_view(), name="how_to_use"),

    # プロジェクト
    path("projects/", ProjectListView.as_view(), name="project_list"),
    path("projects/create/", ProjectCreateView.as_view(), name="project_create"),
    path("projects/<int:pk>/", ProjectDetailView.as_view(), name="project_detail"),
    path("projects/<int:pk>/edit/", ProjectUpdateView.as_view(), name="project_edit"),
    path("projects/<int:pk>/delete/", ProjectDeleteView.as_view(), name="project_delete"),
    path("projects/<int:pk>/pdf/", ProjectPDFView.as_view(), name="project_pdf"),
    path("projects/<int:pk>/gantt_pdf/", GanttPDFView.as_view(), name="project_gantt_pdf"),

    # 共有メモ
    path("projects/<int:pk>/memos/create/", MemoCreateView.as_view(), name="memo_create"),
    path("memos/<int:pk>/edit/", MemoUpdateView.as_view(), name="memo_edit"),

    # チェックリスト
    path("projects/<int:pk>/checklists/create/", ChecklistCreateView.as_view(), name="checklist_create"),
    path("checklist/<int:pk>/edit/", ChecklistUpdateView.as_view(), name="checklist_edit"),

    # チェックリスト項目
    path("checklist/<int:pk>/item/create/", ChecklistItemCreateView.as_view(), name="item_create"),
    path("item/<int:pk>/edit/", ChecklistItemUpdateView.as_view(), name="item_edit"),
    path("item/<int:pk>/toggle/", ChecklistItemToggleView.as_view(), name="item_toggle"),

    # メンバー管理/招待
    path("members/", MemberManagementView.as_view(), name="member_management"),
    path("members/<int:pk>/delete/", MemberDeleteView.as_view(), name="member_delete"),
    path("invitation/accept/<uuid:token>/", AcceptInvitationView.as_view(), name="accept_invitation"),
    path("invitation/<int:pk>/delete/", InvitationDeleteView.as_view(), name="invitation_delete"),

    # ガント/タスク
    path("projects/<int:pk>/tasks.json", ProjectTaskJSONView.as_view(), name="project_tasks_json"),
    path("projects/<int:pk>/task/create/", TaskCreateView.as_view(), name="task_create"),
    path("task/<int:pk>/edit/", TaskUpdateView.as_view(), name="task_edit"),
    path("task/<int:pk>/delete/", TaskDeleteView.as_view(), name="task_delete"),
]