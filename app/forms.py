# app/forms.py

from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import (
    CustomUser,
    Company,
    Project,
    Memo,
    Checklist,
    ChecklistItem,
    Invitation,
    Task,
)


# =========================
# 認証系
# =========================
class CustomAuthenticationForm(AuthenticationForm):
    """既存ビューが参照するログインフォーム名（装飾だけ付与）"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "氏名（ログインID）"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "placeholder": "パスワード"}
        )


class LoginForm(CustomAuthenticationForm):
    """別名で参照されても落ちないように継承"""
    pass


class SignUpForm(forms.Form):
    company_name = forms.CharField(
        label="会社名",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "株式会社 Example"}),
    )
    username = forms.CharField(
        label="氏名（ログインID）",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "鈴木 一郎"}),
    )
    email = forms.EmailField(
        label="メールアドレス",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "suzuki@example.com"}),
    )
    password = forms.CharField(
        label="パスワード",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password_confirm = forms.CharField(
        label="パスワード（確認）",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean_password_confirm(self):
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")
        if password != password_confirm:
            raise forms.ValidationError("パスワードが一致しません。")
        return password_confirm

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("この氏名（ログインID）は既に使用されています。")
        return username


# =========================
# 案件（Project）
#   ※ models.Project は現在:
#     name, start_date, end_date, status, description, company
# =========================
class ProjectForm(forms.ModelForm):
    """作成・更新どちらでも使える汎用フォーム"""
    STATUS_CHOICES = [
        ("", "---------"),
        ("未着工", "未着工"),
        ("進行中", "進行中"),
        ("完了", "完了"),
        ("保留", "保留"),
    ]
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="ステータス",
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Project
        fields = ["name", "status", "start_date", "end_date", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "案件の補足説明"}),
        }
        labels = {
            "name": "案件名",
            "start_date": "開始日",
            "end_date": "終了日",
            "description": "説明",
        }


class ProjectCreateForm(ProjectForm):
    """旧コードが参照しても落ちないように別名を用意"""
    pass


# =========================
# 共有メモ
# =========================
class MemoCreateForm(forms.ModelForm):
    class Meta:
        model = Memo
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "確認事項や申し送りなどを入力..."}
            )
        }
        labels = {"content": ""}


class MemoUpdateForm(MemoCreateForm):
    """旧ビュー互換：更新用フォーム（見た目は作成と同じ）"""
    pass


# =========================
# チェックリスト
# =========================
class ChecklistCreateForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "例：完了確認リスト、安全確認項目など"}
            )
        }
        labels = {"title": "チェックリスト名"}


class ChecklistUpdateForm(ChecklistCreateForm):
    """旧ビュー互換：更新用フォーム"""
    pass


class ChecklistItemForm(forms.ModelForm):
    class Meta:
        model = ChecklistItem
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "新しいタスクを入力"}
            )
        }
        labels = {"title": ""}


class ChecklistItemUpdateForm(ChecklistItemForm):
    """旧ビュー互換：更新用フォーム"""
    pass


# =========================
# 招待
# =========================
class InvitationForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "招待するメンバーのメールアドレス"}
            )
        }
        labels = {"email": "招待メールアドレス"}


class InvitationRegisterForm(forms.Form):
    username = forms.CharField(label="氏名", widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="パスワード", widget=forms.PasswordInput(attrs={"class": "form-control"}))
    password_confirm = forms.CharField(
        label="パスワード（確認）", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    def clean_password_confirm(self):
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")
        if password != password_confirm:
            raise forms.ValidationError("パスワードが一致しません。")
        return password_confirm

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("この氏名は既に使用されています。別の氏名を入力してください。")
        return username


# =========================
# タスク（ガント・依存関係）
# =========================
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["name", "start_date", "end_date", "progress", "dependencies"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "progress": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 100}),
            "dependencies": forms.SelectMultiple(attrs={"class": "form-select", "size": "6"}),
        }
        labels = {
            "name": "タスク名",
            "start_date": "開始日",
            "end_date": "終了日",
            "progress": "進捗率 (%)",
            "dependencies": "先行タスク",
        }

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        # 同一案件内のタスクだけを依存先として選べるように制限
        if project is not None:
            qs = Task.objects.filter(project=project)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            self.fields["dependencies"].queryset = qs


class TaskUpdateForm(TaskForm):
    """旧ビュー互換：更新用フォーム"""
    pass