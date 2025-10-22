from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    Company,
    CustomUser,
    Project,
    Task,
    Memo,
    Checklist,
    ChecklistItem,
    Invitation,
    Customer,
)


# ==========================
# Company
# ==========================
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("id",)


# ==========================
# CustomUser
# ==========================
@admin.register(CustomUser)
class CustomUserAdmin(DjangoUserAdmin):
    """
    以前 list_display に 'role' があり SystemCheckError になっていた。
    'role' はモデルに存在しないため削除し、実在フィールドのみ表示する。
    """

    model = CustomUser

    # 'role' は入れない
    list_display = (
        "id",
        "username",
        "email",
        "company",
        "is_staff",
        "is_superuser",
        "last_login",
    )
    list_filter = ("company", "is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("id",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("個人情報", {"fields": ("first_name", "last_name", "email", "company")}),
        (
            "権限",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("重要な日付", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "company",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                ),
            },
        ),
    )


# ==========================
# Project
# ==========================
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "customer", "company", "start_date", "end_date", "status")
    
    # ★★★ この行を追加 ★★★
    # 一覧画面で編集ページへのリンクにする項目を指定
    list_display_links = ("id", "name")
    
    list_filter = ("company", "status", "customer")
    search_fields = ("name", "description", "customer__name")
    ordering = ("-id",)
    autocomplete_fields = ("company", "customer")


# ==========================
# Customer
# ==========================
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company')
    list_filter = ('company',)
    search_fields = ('name',)
    ordering = ('id',)
    autocomplete_fields = ('company',)


# ==========================
# Task
# ==========================
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "project", "start_date", "end_date", "progress")
    list_filter = ("project",)
    search_fields = ("name",)
    ordering = ("project", "start_date", "id")
    autocomplete_fields = ("project", "dependencies")


# ==========================
# Memo
# ==========================
@admin.register(Memo)
class MemoAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "author", "created_at", "updated_at")
    list_filter = ("project", "author")
    search_fields = ("content",)
    ordering = ("-id",)
    autocomplete_fields = ("project", "author", "mentions")


# ==========================
# Checklist / ChecklistItem
# ==========================
@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "title", "created_at")
    list_filter = ("project",)
    search_fields = ("title",)
    ordering = ("-id",)
    autocomplete_fields = ("project",)


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ("id", "checklist", "title", "is_done", "updated_at")
    list_filter = ("checklist", "is_done")
    search_fields = ("title",)
    ordering = ("checklist", "id")
    autocomplete_fields = ("checklist",)


# ==========================
# Invitation
# ==========================
@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "company", "is_accepted", "created_at", "token")
    list_filter = ("company", "is_accepted")
    search_fields = ("email", "token")
    ordering = ("-id",)
    autocomplete_fields = ("company",)
    readonly_fields = ("token", "created_at")