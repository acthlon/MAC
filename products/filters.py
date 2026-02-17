import django_filters
from rest_framework import filters
from products.models import Products
from core.constants import CATEGORY_CHOICES,RATING_CHOICES


class ProductFilter(django_filters.FilterSet):

    name_search = django_filters.CharFilter(field_name='name',lookup_expr='icontains')
    description_search = django_filters.CharFilter(field_name='description',lookup_expr='icontains')

    max_price = django_filters.NumberFilter(field_name= 'price',lookup_expr='lte',label='All Prices')
    min_prices = django_filters.NumberFilter(field_name='price',lookup_expr='gte',label='All Prices')

    category = django_filters.ChoiceFilter(choices=CATEGORY_CHOICES,lookup_expr='icontains',label='All Category')

    review = django_filters.ChoiceFilter(choices = RATING_CHOICES,label= 'Product Rating')

    class Meta:

        model = Products
        fields = ()