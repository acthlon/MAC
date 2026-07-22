from django import forms

from core.constants import MATERIAL_CATEGORY_CHOICES, PRODUCT_CATEGORY_CHOICES
from core.models import Category


class CategoryAdminForm(forms.ModelForm):
    
    class Meta:
        model = Category
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.target_model:
            if self.instance.target_model.model == 'products':
                self.fields['name'].widget = forms.Select(choices=PRODUCT_CATEGORY_CHOICES)
            elif self.instance.target_model.model == 'materials':
                self.fields['name'].widget = forms.Select(choices=MATERIAL_CATEGORY_CHOICES)