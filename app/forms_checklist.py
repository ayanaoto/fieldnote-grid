from django import forms
from .models import Checklist, ChecklistItem


class ChecklistForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "例）引き渡し前の確認項目",
                    "autocomplete": "off",
                }
            ),
        }
        labels = {
            "title": "チェックリスト名",
        }


class ChecklistItemForm(forms.ModelForm):
    """
    注意:
    ChecklistItem モデルに 'done' 等の真偽値フィールドが無い前提で、title のみを扱います。
    ここを変更するときはモデル側のフィールド名と必ず一致させてください。
    """
    class Meta:
        model = ChecklistItem
        fields = ["title"]  # ← 'done' は含めない（存在しないため）
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "項目名（例：通電確認）",
                    "autocomplete": "off",
                }
            ),
        }
        labels = {
            "title": "項目名",
        }
