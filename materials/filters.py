import django_filters
from materials.models import Materials
from materials.models import CATEGORY_CHOICES



class MaterialsFilter(django_filters.FilterSet):
  
    name_search = django_filters.CharFilter(field_name='name',lok_up = 'icontain')
    description_search = django_filters.CharFilter(field_name = 'description',lookup_expr='icontain')

    min_price = django_filters.NumberFilter(field_name='price',lookup_expr='gte', empty_lable='All Prices')
    max_price = django_filters.NumberFilter(field_name='price',lookup_expr='lte',empty_lable='All Prices')

    quality = django_filters.ChoiceFilter(choices=CATEGORY_CHOICES,empty_label = 'All Qualities')

    class Meta:
        model = Materials
        fields = ('name','description','min_price','max_price')
