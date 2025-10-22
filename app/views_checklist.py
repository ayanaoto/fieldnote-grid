from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .forms import ChecklistItemForm, ChecklistCreateForm, ChecklistUpdateForm
from .models import Checklist, ChecklistItem, Project


class ChecklistCreateView(LoginRequiredMixin, View):
    template_name = "app/checklist_form.html"

    def get_project(self, pk: int) -> Project:
        return get_object_or_404(Project, pk=pk)

    def get(self, request, pk, *args, **kwargs):
        project = self.get_project(pk)
        form = ChecklistCreateForm()
        return render(
            request,
            self.template_name,
            {"form": form, "project": project, "object": None, "mode": "create"},
        )

    def post(self, request, pk, *args, **kwargs):
        project = self.get_project(pk)
        form = ChecklistCreateForm(request.POST)
        if form.is_valid():
            checklist = form.save(commit=False)
            checklist.project = project
            checklist.save()
            return redirect("project_detail", pk=project.pk)
        return render(
            request,
            self.template_name,
            {"form": form, "project": project, "object": None, "mode": "create"},
        )


class ChecklistUpdateView(LoginRequiredMixin, View):
    template_name = "app/checklist_form.html"

    def get_object(self, pk: int) -> Checklist:
        return get_object_or_404(Checklist, pk=pk)

    def get(self, request, pk, *args, **kwargs):
        checklist = self.get_object(pk)
        form = ChecklistUpdateForm(instance=checklist)
        return render(
            request,
            self.template_name,
            {"form": form, "project": checklist.project, "object": checklist, "mode": "edit"},
        )

    def post(self, request, pk, *args, **kwargs):
        checklist = self.get_object(pk)
        form = ChecklistUpdateForm(request.POST, instance=checklist)
        if form.is_valid():
            form.save()
            return redirect("project_detail", pk=checklist.project_id)
        return render(
            request,
            self.template_name,
            {"form": form, "project": checklist.project, "object": checklist, "mode": "edit"},
        )


class ChecklistItemCreateView(LoginRequiredMixin, View):
    """
    新旧どちらのURL形でも動くように、checklist_id または pk のどちらでも受け取る。
    /checklist/<checklist_id>/items/add/
    /checklist/<pk>/item/create/
    """
    template_name = "app/checklist_item_form.html"

    def _resolve_checklist_id(self, **kwargs) -> int:
        return kwargs.get("checklist_id") or kwargs.get("pk")

    def get(self, request, *args, **kwargs):
        checklist_id = self._resolve_checklist_id(**kwargs)
        checklist = get_object_or_404(Checklist, pk=checklist_id)
        form = ChecklistItemForm()
        return render(
            request,
            self.template_name,
            {"form": form, "checklist": checklist, "object": None, "mode": "create"},
        )

    def post(self, request, *args, **kwargs):
        checklist_id = self._resolve_checklist_id(**kwargs)
        checklist = get_object_or_404(Checklist, pk=checklist_id)
        form = ChecklistItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.checklist = checklist
            item.save()
            return redirect("project_detail", pk=checklist.project_id)
        return render(
            request,
            self.template_name,
            {"form": form, "checklist": checklist, "object": None, "mode": "create"},
        )


class ChecklistItemUpdateView(LoginRequiredMixin, View):
    template_name = "app/checklist_item_form.html"

    def get_object(self, pk: int) -> ChecklistItem:
        return get_object_or_404(ChecklistItem, pk=pk)

    def get(self, request, pk, *args, **kwargs):
        item = self.get_object(pk)
        form = ChecklistItemForm(instance=item)
        return render(
            request,
            self.template_name,
            {"form": form, "checklist": item.checklist, "object": item, "mode": "edit"},
        )

    def post(self, request, pk, *args, **kwargs):
        item = self.get_object(pk)
        form = ChecklistItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect("project_detail", pk=item.checklist.project_id)
        return render(
            request,
            self.template_name,
            {"form": form, "checklist": item.checklist, "object": item, "mode": "edit"},
        )


class ChecklistItemToggleView(LoginRequiredMixin, View):
    """
    チェックのON/OFF切り替え（POST専用）
    """
    def post(self, request, pk, *args, **kwargs):
        item = get_object_or_404(ChecklistItem, pk=pk)
        item.is_done = not item.is_done
        item.save(update_fields=["is_done", "updated_at"])
        return redirect("project_detail", pk=item.checklist.project_id)