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
        return self.request.user.is_authenticated and self.request.user.is_staff


# ------------------------------------------------------------
# 認証 & トップ
# ------------------------------------------------------------
class SignUpView(View):
    template_name = "app/signup.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return render(request, self.template_name, {"form": SignUpForm()})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = SignUpForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        company_name = form.cleaned_data["company_name"]
        username = form.cleaned_data["username"]
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]

        company = Company.objects.create(name=company_name)
        user = CustomUser.objects.create_user(
            username=username, email=email, password=password, company=company, is_staff=True
        )
        login(request, user)
        return redirect("home")


class CustomLoginView(LoginView):
    template_name = "app/login.html"
    authentication_form = CustomAuthenticationForm


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("login")


class HomeView(LoginRequiredMixin, View):
    """ホーム画面をダッシュボードとして機能させるビュー"""
    template_name = "app/home.html"

    def get(self, request, *args, **kwargs):
        company = request.user.company
        
        # --- ダッシュボード用のデータを取得 ---
        
        # 1. 進行中の案件数
        project_count = Project.objects.filter(company=company, status="進行中").count()
        
        # 2. 期限切れ or 期限間近の未完了タスク (7日以内)
        today = timezone.now().date()
        due_date_limit = today + timezone.timedelta(days=7)
        overdue_tasks = Task.objects.filter(
            project__company=company,
            end_date__lte=due_date_limit, # 7日以内 or 過去
            progress__lt=100
        ).select_related('project').order_by('end_date')

        # ★★★ 期限が近いタスクの件数を取得 ★★★
        overdue_task_count = overdue_tasks.count()

        # 3. 最近の共有メモ
        recent_memos = (
            Memo.objects.filter(project__company=company)
            .select_related("project", "author")
            .order_by("-id")[:5] # 5件に制限
        )
        
        context = {
            "project_count": project_count,
            "overdue_task_count": overdue_task_count, # ★ コンテキストに追加
            "overdue_tasks": overdue_tasks,
            "recent_memos": recent_memos,
            "today": today,
        }
        
        return render(request, self.template_name, context)


# ------------------------------------------------------------
# 使い方ガイド
# ------------------------------------------------------------
class HowToUseView(LoginRequiredMixin, TemplateView):
    """「使い方ガイド」ページを表示するためのビュー"""
    template_name = "app/how_to_use.html"


# ------------------------------------------------------------
# プロジェクト
# ------------------------------------------------------------
class ProjectListView(LoginRequiredMixin, ListView):
    template_name = "app/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        return Project.objects.filter(company=self.request.user.company).order_by("-id")


class ProjectCreateView(AdminRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "app/project_create.html"

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.company = self.request.user.company
        obj.save()
        return redirect("project_detail", pk=obj.pk)


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = "app/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return Project.objects.filter(company=self.request.user.company)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project: Project = self.object
        ctx["memos"] = (
            Memo.objects.filter(project=project)
            .select_related("author")
            .prefetch_related("mentions")
            .order_by("-id")
        )
        ctx["checklists"] = (
            Checklist.objects.filter(project=project)
            .prefetch_related("items")
            .order_by("-id")
        )
        ctx["task_form"] = TaskForm(project=project)
        ctx["checklist_item_form"] = ChecklistItemForm()
        ctx["memo_form"] = MemoCreateForm()
        ctx["checklist_form"] = ChecklistCreateForm()
        return ctx


class ProjectUpdateView(AdminRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "app/project_edit.html"

    def get_queryset(self):
        return Project.objects.filter(company=self.request.user.company)

    def get_success_url(self):
        return reverse("project_detail", args=[self.object.pk])


class ProjectDeleteView(AdminRequiredMixin, DeleteView):
    model = Project
    template_name = "app/project_confirm_delete.html"
    success_url = reverse_lazy("project_list")

    def get_queryset(self):
        return Project.objects.filter(company=self.request.user.company)


# ------------------------------------------------------------
# メンバー管理 / 招待
# ------------------------------------------------------------
class MemberManagementView(AdminRequiredMixin, View):
    template_name = "app/member_management.html"

    def get(self, request, *args, **kwargs):
        company = request.user.company
        members = CustomUser.objects.filter(company=company).order_by("id")
        invitations = Invitation.objects.filter(company=company, is_accepted=False).order_by("-id")
        form = InvitationForm()
        return render(
            request,
            self.template_name,
            {"members": members, "invitations": invitations, "form": form},
        )

    def post(self, request, *args, **kwargs):
        form = InvitationForm(request.POST)
        company = request.user.company
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.company = company
            invitation.save()
            try:
                accept_url = request.build_absolute_uri(
                    reverse_lazy("accept_invitation", kwargs={"token": invitation.token})
                )
                subject = f"{company.name} から FieldNote に招待されました"
                message = (
                    f"{company.name} から FieldNote に招待されました。\n"
                    f"以下のリンクをクリックして登録を完了してください。\n\n{accept_url}\n"
                )
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [invitation.email])
            except Exception as e:
                print("メールの送信に失敗:", e)
            return redirect("member_management")

        members = CustomUser.objects.filter(company=company).order_by("id")
        invitations = Invitation.objects.filter(company=company, is_accepted=False).order_by("-id")
        return render(
            request,
            self.template_name,
            {"members": members, "invitations": invitations, "form": form},
        )


class AcceptInvitationView(View):
    template_name = "app/accept_invitation.html"

    def get(self, request, token, *args, **kwargs):
        invitation = get_object_or_404(Invitation, token=token)
        return render(request, self.template_name, {"invitation": invitation})

    @transaction.atomic
    def post(self, request, token, *args, **kwargs):
        invitation = get_object_or_404(Invitation, token=token)
        if invitation.is_accepted:
            return redirect("login")
        username = request.POST.get("username") or invitation.email.split("@")[0]
        password = request.POST.get("password")
        if not password:
            return render(
                request,
                self.template_name,
                {"invitation": invitation, "error": "パスワードを入力してください"},
            )
        user = CustomUser.objects.create_user(
            username=username,
            email=invitation.email,
            password=password,
            company=invitation.company,
        )
        invitation.is_accepted = True
        invitation.save(update_fields=["is_accepted"])
        login(request, user)
        return redirect("home")


class MemberDeleteView(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        member = get_object_or_404(
            CustomUser,
            pk=self.kwargs["pk"],
            company=request.user.company,
        )
        if member.pk == request.user.pk:
            return redirect("member_management")
        member.delete()
        return redirect("member_management")


class InvitationDeleteView(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        inv = get_object_or_404(
            Invitation,
            pk=self.kwargs["pk"],
            company=self.request.user.company,
            is_accepted=False,
        )
        inv.delete()
        return redirect("member_management")


# ------------------------------------------------------------
# ガントチャート用 JSON
# ------------------------------------------------------------
class ProjectTaskJSONView(LoginRequiredMixin, View):
    """Frappe Gantt などで参照するタスク JSON"""

    def get(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs["pk"], company=request.user.company)
        tasks_qs = (
            Task.objects.filter(project=project)
            .prefetch_related("dependencies")
            .order_by("start_date", "end_date", "id")
        )

        data = []
        for t in tasks_qs:
            deps = []
            if hasattr(t, "dependencies"):
                deps = [str(d.id) for d in t.dependencies.all()]
            data.append(
                {
                    "id": str(t.id),
                    "name": getattr(t, "name", "") or "",
                    "start": (t.start_date.isoformat() if getattr(t, "start_date", None) else None),
                    "end": (t.end_date.isoformat() if getattr(t, "end_date", None) else None),
                    "progress": int(getattr(t, "progress", 0) or 0),
                    "dependencies": ",".join(deps),
                }
            )
        return JsonResponse(data, safe=False)


# ------------------------------------------------------------
# PDF出力
# ------------------------------------------------------------
class ProjectPDFView(LoginRequiredMixin, View):
    """案件サマリーをPDFで出力するビュー"""

    def get(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project,
            pk=self.kwargs["pk"],
            company=request.user.company
        )
        context = {"project": project}
        html_string = render_to_string("app/project_pdf.html", context)
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
        response = HttpResponse(pdf_file, content_type="application/pdf")
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
        svg_data = request.POST.get('svg_data', '')
        context = {
            "project": project,
            "svg_data": svg_data,
        }
        html_string = render_to_string("app/gantt_pdf.html", context)
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
        response = HttpResponse(pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="gantt_{project.pk}_{project.name}.pdf"'
        return response

