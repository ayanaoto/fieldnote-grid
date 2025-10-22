from __future__ import annotations

import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


# =========================================
# 会社
# =========================================
class Company(models.Model):
    name = models.CharField("会社名", max_length=255, unique=True)

    class Meta:
        verbose_name = "会社"
        verbose_name_plural = "会社"

    def __str__(self) -> str:
        return self.name


# =========================================
# ★★★★★ 新規追加: 顧客モデル ★★★★★
# =========================================
class Customer(models.Model):
    company = models.ForeignKey(Company, verbose_name="所属会社", on_delete=models.CASCADE, related_name="customers")
    name = models.CharField("顧客名", max_length=255)
    # 必要に応じて、電話番号や住所などのフィールドもここに追加できます
    # tel = models.CharField("電話番号", max_length=20, blank=True)
    # address = models.CharField("住所", max_length=255, blank=True)

    class Meta:
        verbose_name = "顧客"
        verbose_name_plural = "顧客"
        # 会社ごとに顧客名はユニークにする
        unique_together = ('company', 'name')

    def __str__(self) -> str:
        return self.name


# =========================================
# ユーザー（カスタム）
# =========================================
class CustomUser(AbstractUser):
    company = models.ForeignKey(
        Company,
        verbose_name="所属会社",
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "ユーザー"
        verbose_name_plural = "ユーザー"

    def __str__(self) -> str:
        return self.get_full_name() or self.username


# =========================================
# 招待
# =========================================
class Invitation(models.Model):
    token = models.UUIDField("トークン", default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField("メールアドレス")
    company = models.ForeignKey(Company, verbose_name="会社", on_delete=models.CASCADE, related_name="invitations")
    is_accepted = models.BooleanField("承認済み", default=False)
    created_at = models.DateTimeField("作成日時", default=timezone.now)

    class Meta:
        verbose_name = "招待"
        verbose_name_plural = "招待"

    def __str__(self) -> str:
        status = "済" if self.is_accepted else "未"
        return f"{self.email} ({status})"


# =========================================
# 案件（Project）
# =========================================
class Project(models.Model):
    company = models.ForeignKey(Company, verbose_name="会社", on_delete=models.CASCADE, related_name="projects")
    
    # ★★★★★ ここに customer フィールドを追加 ★★★★★
    customer = models.ForeignKey(
        Customer,
        verbose_name="顧客",
        on_delete=models.SET_NULL,  # 顧客が削除されても案件は消えないようにする
        null=True,
        blank=True,
        related_name="projects",
    )
    
    name = models.CharField("案件名", max_length=255)
    start_date = models.DateField("開始日", null=True, blank=True)
    end_date = models.DateField("終了日", null=True, blank=True)
    status = models.CharField("ステータス", max_length=50, blank=True)
    description = models.TextField("説明", blank=True, default="")
    created_at = models.DateTimeField("作成日時", auto_now_add=True)

    class Meta:
        ordering = ("-id",)
        verbose_name = "案件"
        verbose_name_plural = "案件"

    def __str__(self) -> str:
        return self.name


# =========================================
# タスク（ガント用）
# =========================================
class Task(models.Model):
    project = models.ForeignKey(Project, verbose_name="案件", on_delete=models.CASCADE, related_name="tasks")
    name = models.CharField("タスク名", max_length=255)
    start_date = models.DateField("開始日", null=True, blank=True)
    end_date = models.DateField("終了日", null=True, blank=True)
    progress = models.PositiveIntegerField("進捗(%)", default=0)  # 0-100 想定

    dependencies = models.ManyToManyField(
        "self",
        verbose_name="依存タスク",
        symmetrical=False,
        blank=True,
        related_name="dependents",
    )

    # 既存行に入るよう default を付与
    created_at = models.DateTimeField("作成日時", default=timezone.now, editable=False)

    class Meta:
        ordering = ("start_date", "end_date", "id")
        verbose_name = "タスク"
        verbose_name_plural = "タスク"

    def __str__(self) -> str:
        return f"{self.project.name} / {self.name}"


# =========================================
# 共有メモ
# =========================================
class Memo(models.Model):
    project = models.ForeignKey(Project, verbose_name="案件", on_delete=models.CASCADE, related_name="memos")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="作成者",
        on_delete=models.SET_NULL,
        null=True,
        related_name="memos",
    )
    content = models.TextField("内容")

    mentions = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="メンション",
        blank=True,
        related_name="mentioned_in",
    )

    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        ordering = ("-id",)
        verbose_name = "共有メモ"
        verbose_name_plural = "共有メモ"

    def __str__(self) -> str:
        return f"Memo({self.project.name})"


# =========================================
# チェックリスト
# =========================================
class Checklist(models.Model):
    project = models.ForeignKey(Project, verbose_name="案件", on_delete=models.CASCADE, related_name="checklists")
    # 既存行配慮のため空文字を許容
    title = models.CharField("タイトル", max_length=255, blank=True, default="")
    created_at = models.DateTimeField("作成日時", auto_now_add=True)

    class Meta:
        ordering = ("-id",)
        verbose_name = "チェックリスト"
        verbose_name_plural = "チェックリスト"

    def __str__(self) -> str:
        return f"{self.project.name} / {self.title}"


class ChecklistItem(models.Model):
    checklist = models.ForeignKey(Checklist, verbose_name="チェックリスト", on_delete=models.CASCADE, related_name="items")
    # 既存行配慮のため空文字を許容
    title = models.CharField("項目名", max_length=255, blank=True, default="")
    is_done = models.BooleanField("完了", default=False)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        ordering = ("id",)
        verbose_name = "チェック項目"
        verbose_name_plural = "チェック項目"

    def __str__(self) -> str:
        return self.title