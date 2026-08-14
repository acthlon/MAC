from django import forms

from core.choices import MaterialCategory, ProductCategory
from core.models import Category


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.target_model:
            if self.instance.target_model.model == "products":
                self.fields["name"].widget = forms.Select(
                    choices=ProductCategory.choices
                )
            elif self.instance.target_model.model == "materials":
                self.fields["name"].widget = forms.Select(
                    choices=MaterialCategory.choices
                )
