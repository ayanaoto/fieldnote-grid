# app/views_memo.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from .models import Project, Memo
from .forms import MemoCreateForm  # Updateも同フォームを使う


class MemoCreateView(LoginRequiredMixin, View):
    template_name = "app/memo_form.html"

    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        form = MemoCreateForm()
        # テンプレが object.project を参照しても壊れないようダミーを渡す
        dummy = Memo(project=project, author=request.user, content="")
        return render(
            request,
            self.template_name,
            {"form": form, "project": project, "object": dummy, "mode": "create"},
        )

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        form = MemoCreateForm(request.POST)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.project = project
            memo.author = request.user
            memo.save()
            form.save_m2m()  # 将来 mentions をフォーム化した場合の保険
            return redirect("project_detail", pk=project.pk)

        dummy = Memo(project=project, author=request.user, content="")
        return render(
            request,
            self.template_name,
            {"form": form, "project": project, "object": dummy, "mode": "create"},
        )


class MemoUpdateView(LoginRequiredMixin, View):
    template_name = "app/memo_form.html"

    def get(self, request, pk):
        memo = get_object_or_404(Memo, pk=pk)
        form = MemoCreateForm(instance=memo)
        project = memo.project
        return render(
            request,
            self.template_name,
            {"form": form, "project": project, "object": memo, "mode": "edit"},
        )

    def post(self, request, pk):
        memo = get_object_or_404(Memo, pk=pk)
        form = MemoCreateForm(request.POST, instance=memo)
        if form.is_valid():
            form.save()
            return redirect("project_detail", pk=memo.project.pk)

        return render(
            request,
            self.template_name,
            {"form": form, "project": memo.project, "object": memo, "mode": "edit"},
        )
