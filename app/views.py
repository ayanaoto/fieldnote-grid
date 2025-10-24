# app/views.py

from __future__ import annotations

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.mail import send_mail
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    DeleteView,
    UpdateView,
    TemplateView,
)
from django.utils import timezone # ダッシュボード機能のために追加

# PDF生成ライブラリをインポート
from django.template.loader import render_to_string
from weasyprint import HTML

from .models import (
    Company,
    CustomUser,
    Project,
    Task,
    Memo,
    Checklist,
    ChecklistItem,
    Invitation,
)

from .forms import (
    SignUpForm,
    CustomAuthenticationForm,
    ProjectForm,
    MemoCreateForm,
    ChecklistCreateForm,
    ChecklistItemForm,
    InvitationForm,
    TaskForm,
    MemoUpdateForm,
    ChecklistUpdateForm,
    ChecklistItemUpdateForm,
)


# ------------------------------------------------------------
# 共通ミックスイン
# ------------------------------------------------------------
class AdminRequiredMixin(UserPassesTestMixin):
    """is_staff の管理者権限を要求"""

    def test_func(self):
        # ユーザーが認証済みで、かつスタッフ権限を持っているか確認
        return self.request.user.is_authenticated and self.request.user.is_staff


# ------------------------------------------------------------
# 認証 & トップ
# ------------------------------------------------------------
class SignUpView(View):
    """新規登録ビュー"""
    template_name = "app/signup.html"

    def get(self, request, *args, **kwargs):
        # ログイン済みならホームページへリダイレクト
        if request.user.is_authenticated:
            return redirect("home")
        # 未ログインなら登録フォームを表示
        return render(request, self.template_name, {"form": SignUpForm()})

    @transaction.atomic # 会社とユーザー作成をトランザクション化
    def post(self, request, *args, **kwargs):
        form = SignUpForm(request.POST)
        # フォームが無効ならエラーメッセージと共に再表示
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        # フォームからデータを取得
        company_name = form.cleaned_data["company_name"]
        username = form.cleaned_data["username"]
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]

        # 会社を作成
        company = Company.objects.create(name=company_name)
        # ユーザーを作成 (最初のユーザーは管理者 = is_staff=True)
        user = CustomUser.objects.create_user(
            username=username, email=email, password=password, company=company, is_staff=True
        )
        # 作成したユーザーでログイン
        login(request, user)
        # ホームページへリダイレクト
        return redirect("home")


class CustomLoginView(LoginView):
    """カスタムログインビュー"""
    template_name = "app/login.html"
    authentication_form = CustomAuthenticationForm # カスタムフォームを使用


class CustomLogoutView(LogoutView):
    """ログアウトビュー"""
    next_page = reverse_lazy("login") # ログアウト後はログインページへ


class HomeView(LoginRequiredMixin, View):
    """ホーム画面（ダッシュボード）ビュー"""
    template_name = "app/home.html"

    def get(self, request, *args, **kwargs):
        company = request.user.company # ログインユーザーの所属会社を取得

        # --- ダッシュボード用のデータを取得 ---

        # 1. 進行中の案件数を取得
        project_count = Project.objects.filter(company=company, status="進行中").count()

        # 2. 期限切れ or 7日以内に期限が来る未完了タスクを取得
        today = timezone.now().date()
        due_date_limit = today + timezone.timedelta(days=7)
        overdue_tasks = Task.objects.filter(
            project__company=company,   # ログインユーザーの会社のタスク
            end_date__lte=due_date_limit, # 期限が7日以内または過去
            progress__lt=100            # 未完了 (進捗100%未満)
        ).select_related('project').order_by('end_date') # プロジェクト情報も取得し、期限日でソート

        # 期限が近いタスクの件数を取得
        overdue_task_count = overdue_tasks.count()

        # 3. 最近共有されたメモを5件取得
        recent_memos = (
            Memo.objects.filter(project__company=company) # ログインユーザーの会社のメモ
            .select_related("project", "author") # プロジェクトと作成者の情報も取得
            .order_by("-id")[:5] # 新しい順に5件
        )

        # テンプレートに渡すコンテキストデータを作成
        context = {
            "project_count": project_count,
            "overdue_task_count": overdue_task_count,
            "overdue_tasks": overdue_tasks,
            "recent_memos": recent_memos,
            "today": today, # テンプレートで今日の日付を使うため
        }

        # テンプレートを描画して返す
        return render(request, self.template_name, context)


# ------------------------------------------------------------
# 使い方ガイド
# ------------------------------------------------------------
class HowToUseView(LoginRequiredMixin, TemplateView):
    """「使い方ガイド」ページを表示するためのビュー"""
    template_name = "app/how_to_use.html"


# ------------------------------------------------------------
# プロジェクト関連ビュー
# ------------------------------------------------------------
class ProjectListView(LoginRequiredMixin, ListView):
    """プロジェクト一覧ビュー"""
    template_name = "app/project_list.html"
    context_object_name = "projects" # テンプレートでの変数名

    def get_queryset(self):
        # ログインユーザーの会社のプロジェクトを新しい順に取得
        return Project.objects.filter(company=self.request.user.company).order_by("-id")


class ProjectCreateView(AdminRequiredMixin, CreateView):
    """プロジェクト作成ビュー (管理者のみ)"""
    model = Project
    form_class = ProjectForm # 使用するフォームを指定
    template_name = "app/project_create.html"

    def form_valid(self, form):
        # フォームが有効な場合の処理
        obj = form.save(commit=False) # まだDBには保存しない
        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
        # IntegrityError 修正：プロジェクトに会社情報を紐付ける
        obj.company = self.request.user.company
        # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
        obj.save() # DBに保存
        # 作成したプロジェクトの詳細ページへリダイレクト
        return redirect("project_detail", pk=obj.pk)


class ProjectDetailView(LoginRequiredMixin, DetailView):
    """プロジェクト詳細ビュー"""
    model = Project
    template_name = "app/project_detail.html"
    context_object_name = "project" # テンプレートでの変数名

    def get_queryset(self):
        # ログインユーザーの会社のプロジェクトのみ表示可能にする
        return Project.objects.filter(company=self.request.user.company)

    def get_context_data(self, **kwargs):
        # 詳細ページで表示する追加情報をコンテキストに追加
        ctx = super().get_context_data(**kwargs)
        project: Project = self.object # 現在表示しているプロジェクトオブジェクト
        # 関連するメモを新しい順に取得 (作成者情報も)
        ctx["memos"] = (
            Memo.objects.filter(project=project)
            .select_related("author")
            .prefetch_related("mentions") # パフォーマンス改善: メンション情報を先読み
            .order_by("-id")
        )
        # 関連するチェックリストを新しい順に取得 (アイテム情報も)
        ctx["checklists"] = (
            Checklist.objects.filter(project=project)
            .prefetch_related("items") # パフォーマンス改善: アイテム情報を先読み
            .order_by("-id")
        )
        # 各種作成フォームをコンテキストに追加
        ctx["task_form"] = TaskForm(project=project) # タスクフォームにはプロジェクト情報が必要
        ctx["checklist_item_form"] = ChecklistItemForm()
        ctx["memo_form"] = MemoCreateForm()
        ctx["checklist_form"] = ChecklistCreateForm()
        return ctx


class ProjectUpdateView(AdminRequiredMixin, UpdateView):
    """プロジェクト編集ビュー (管理者のみ)"""
    model = Project
    form_class = ProjectForm
    template_name = "app/project_edit.html"

    def get_queryset(self):
        # ログインユーザーの会社のプロジェクトのみ編集可能にする
        return Project.objects.filter(company=self.request.user.company)

    def get_success_url(self):
        # 編集成功後は詳細ページへリダイレクト
        return reverse("project_detail", args=[self.object.pk])


class ProjectDeleteView(AdminRequiredMixin, DeleteView):
    """プロジェクト削除ビュー (管理者のみ)"""
    model = Project
    template_name = "app/project_confirm_delete.html" # 削除確認テンプレート
    success_url = reverse_lazy("project_list") # 削除成功後は一覧ページへ

    def get_queryset(self):
        # ログインユーザーの会社のプロジェクトのみ削除可能にする
        return Project.objects.filter(company=self.request.user.company)


# ------------------------------------------------------------
# メンバー管理 / 招待関連ビュー
# ------------------------------------------------------------
class MemberManagementView(AdminRequiredMixin, View):
    """メンバー管理ビュー (管理者のみ)"""
    template_name = "app/member_management.html"

    def get(self, request, *args, **kwargs):
        # GETリクエスト時の処理 (一覧表示)
        company = request.user.company
        # 所属メンバー一覧を取得
        members = CustomUser.objects.filter(company=company).order_by("id")
        # 未承諾の招待一覧を取得
        invitations = Invitation.objects.filter(company=company, is_accepted=False).order_by("-id")
        # 招待フォームを準備
        form = InvitationForm()
        return render(
            request,
            self.template_name,
            {"members": members, "invitations": invitations, "form": form},
        )

    def post(self, request, *args, **kwargs):
        # POSTリクエスト時の処理 (招待メール送信)
        form = InvitationForm(request.POST)
        company = request.user.company
        if form.is_valid():
            # フォームが有効なら招待を作成
            invitation = form.save(commit=False)
            invitation.company = company # 会社情報を設定
            invitation.save()
            try:
                # 招待承諾用のURLを生成
                accept_url = request.build_absolute_uri(
                    reverse_lazy("accept_invitation", kwargs={"token": invitation.token})
                )
                subject = f"{company.name} から FieldNote に招待されました"
                message = (
                    f"{company.name} から FieldNote に招待されました。\n"
                    f"以下のリンクをクリックして登録を完了してください。\n\n{accept_url}\n"
                )
                # 招待メールを送信
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [invitation.email])
            except Exception as e:
                # メール送信失敗時のログ出力 (本番ではより詳細なエラーハンドリング推奨)
                print("メールの送信に失敗:", e)
            # 成功したらメンバー管理ページへリダイレクト
            return redirect("member_management")

        # フォームが無効ならエラーメッセージと共に再表示
        members = CustomUser.objects.filter(company=company).order_by("id")
        invitations = Invitation.objects.filter(company=company, is_accepted=False).order_by("-id")
        return render(
            request,
            self.template_name,
            {"members": members, "invitations": invitations, "form": form},
        )


class AcceptInvitationView(View):
    """招待承諾ビュー"""
    template_name = "app/accept_invitation.html"

    def get(self, request, token, *args, **kwargs):
        # GETリクエスト: 招待情報が見つかれば登録フォームを表示
        invitation = get_object_or_404(Invitation, token=token)
        return render(request, self.template_name, {"invitation": invitation})

    @transaction.atomic # ユーザー作成と招待更新をトランザクション化
    def post(self, request, token, *args, **kwargs):
        # POSTリクエスト: ユーザー登録処理
        invitation = get_object_or_404(Invitation, token=token)
        # 既に承諾済みならログインページへ
        if invitation.is_accepted:
            return redirect("login")

        # フォームからユーザー名とパスワードを取得
        # ユーザー名がなければメールアドレスの@より前を使う
        username = request.POST.get("username") or invitation.email.split("@")[0]
        password = request.POST.get("password")
        # パスワードがなければエラー
        if not password:
            return render(
                request,
                self.template_name,
                {"invitation": invitation, "error": "パスワードを入力してください"},
            )
        # 新しいユーザーを作成
        user = CustomUser.objects.create_user(
            username=username,
            email=invitation.email,
            password=password,
            company=invitation.company, # 招待元の会社に所属させる
        )
        # 招待を承諾済みに更新
        invitation.is_accepted = True
        invitation.save(update_fields=["is_accepted"])
        # 作成したユーザーでログイン
        login(request, user)
        # ホームページへリダイレクト
        return redirect("home")


class MemberDeleteView(AdminRequiredMixin, View):
    """メンバー削除ビュー (管理者のみ)"""
    def post(self, request, *args, **kwargs):
        member = get_object_or_404(
            CustomUser,
            pk=self.kwargs["pk"], # URLからメンバーIDを取得
            company=request.user.company, # ログインユーザーと同じ会社か確認
        )
        # 自分自身は削除できないようにする
        if member.pk == request.user.pk:
            return redirect("member_management")
        member.delete()
        return redirect("member_management")


class InvitationDeleteView(AdminRequiredMixin, View):
    """招待削除ビュー (管理者のみ)"""
    def post(self, request, *args, **kwargs):
        inv = get_object_or_404(
            Invitation,
            pk=self.kwargs["pk"], # URLから招待IDを取得
            company=self.request.user.company, # ログインユーザーと同じ会社か確認
            is_accepted=False, # 未承諾のもののみ削除可能
        )
        inv.delete()
        return redirect("member_management")


# ------------------------------------------------------------
# ガントチャート用 JSON ビュー
# ------------------------------------------------------------
class ProjectTaskJSONView(LoginRequiredMixin, View):
    """特定のプロジェクトのタスク情報をJSON形式で返すビュー (ガントチャートライブラリ用)"""

    def get(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs["pk"], company=request.user.company)
        tasks_qs = (
            Task.objects.filter(project=project)
            .prefetch_related("dependencies") # パフォーマンス改善: 依存タスク情報を先読み
            .order_by("start_date", "end_date", "id") # ガントチャート表示に適した順序
        )

        # Frappe Gantt ライブラリが要求する形式にデータを変換
        data = []
        for t in tasks_qs:
            deps = []
            # 依存タスクIDのリストを作成
            if hasattr(t, "dependencies"):
                deps = [str(d.id) for d in t.dependencies.all()]
            data.append(
                {
                    "id": str(t.id),
                    "name": getattr(t, "name", "") or "", # タスク名 (空の場合も考慮)
                    "start": (t.start_date.isoformat() if getattr(t, "start_date", None) else None), # 開始日 (ISO形式)
                    "end": (t.end_date.isoformat() if getattr(t, "end_date", None) else None), # 終了日 (ISO形式)
                    "progress": int(getattr(t, "progress", 0) or 0), # 進捗率 (整数)
                    "dependencies": ",".join(deps), # 依存タスクID (カンマ区切り文字列)
                }
            )
        # JSONレスポンスとして返す (リストなので safe=False)
        return JsonResponse(data, safe=False)


# ------------------------------------------------------------
# PDF出力ビュー
# ------------------------------------------------------------
class ProjectPDFView(LoginRequiredMixin, View):
    """案件サマリーをPDFで出力するビュー"""

    def get(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project,
            pk=self.kwargs["pk"],
            company=request.user.company
        )
        # PDF生成用のHTMLテンプレートを描画
        context = {"project": project}
        html_string = render_to_string("app/project_pdf.html", context)
        # WeasyPrint を使ってHTMLからPDFを生成
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
        # PDFファイルをHttpResponseとして返す
        response = HttpResponse(pdf_file, content_type="application/pdf")
        # ダウンロード時のファイル名を指定
        response["Content-Disposition"] = f'attachment; filename="project_{project.pk}_{project.name}.pdf"'
        return response


class GanttPDFView(LoginRequiredMixin, View):
    """工程表（ガントチャート）をPDFで出力するビュー"""

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project,
            pk=self.kwargs["pk"],
            company=request.user.company
        )
        # JavaScriptから送られてきたSVGデータを取得
        svg_data = request.POST.get('svg_data', '')
        # PDF生成用のHTMLテンプレートを描画
        context = {
            "project": project,
            "svg_data": svg_data, # SVGデータをテンプレートに渡す
        }
        html_string = render_to_string("app/gantt_pdf.html", context)
        # WeasyPrint を使ってHTMLからPDFを生成
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
        # PDFファイルをHttpResponseとして返す
        response = HttpResponse(pdf_file, content_type="application/pdf")
        # ダウンロード時のファイル名を指定
        response["Content-Disposition"] = f'attachment; filename="gantt_{project.pk}_{project.name}.pdf"'
        return response

