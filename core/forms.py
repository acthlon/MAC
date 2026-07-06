from django import forms
from core.models import Category
from core.constants import PRODUCT_CATEGORY_CHOICES, MATERIAL_CATEGORY_CHOICES

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