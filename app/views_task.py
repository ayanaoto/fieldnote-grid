# app/views_task.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from .models import Project, Task
from .forms import TaskForm


class TaskCreateView(LoginRequiredMixin, View):
    template_name = "app/task_form.html"

    # 引数名を 'project_pk' から 'pk' に変更
    def get(self, request, pk):
        # 変数名も 'project_pk' から 'pk' に変更
        project = get_object_or_404(Project, pk=pk)
        form = TaskForm(project=project)
        # テンプレの互換確保（object.project.pk を参照してもOK）
        dummy = Task(project=project, name="", progress=0)
        return render(
            request,
            self.template_name,
            {"form": form, "project": project, "object": dummy, "mode": "create"},
        )

    # 引数名を 'project_pk' から 'pk' に変更
    def post(self, request, pk):
        # 変数名も 'project_pk' から 'pk' に変更
        project = get_object_or_404(Project, pk=pk)
        form = TaskForm(request.POST, project=project)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()
            form.save_m2m()  # dependencies
            return redirect("project_detail", pk=project.pk)

        dummy = Task(project=project, name="", progress=0)
        return render(
            request,
            self.template_name,
            {"form": form, "project": project, "object": dummy, "mode": "create"},
        )


class TaskUpdateView(LoginRequiredMixin, View):
    template_name = "app/task_form.html"

    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        form = TaskForm(instance=task, project=task.project)
        return render(
            request,
            self.template_name,
            {"form": form, "project": task.project, "object": task, "mode": "edit"},
        )

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        form = TaskForm(request.POST, instance=task, project=task.project)
        if form.is_valid():
            form.save()
            return redirect("project_detail", pk=task.project.pk)

        return render(
            request,
            self.template_name,
            {"form": form, "project": task.project, "object": task, "mode": "edit"},
        )


class TaskDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        project_pk = task.project.pk
        task.delete()
        return redirect("project_detail", pk=project_pk)