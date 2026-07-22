import django_filters
from rest_framework import filters

from core.constants import (PRODUCT_CATEGORY_CHOICES, PRODUCT_SIZE_CHOICES,
                            QUALITY_CHOICES, RATING_CHOICES)
from products.models import Products


class ProductFilter(django_filters.FilterSet):

    name_search = django_filters.CharFilter(field_name='name',lookup_expr='icontains')
    description_search = django_filters.CharFilter(field_name='description',lookup_expr='icontains')

    max_price = django_filters.NumberFilter(field_name= 'price',lookup_expr='lte',label='All Prices')
    min_prices = django_filters.NumberFilter(field_name='price',lookup_expr='gte',label='All Prices')

    quality_category = django_filters.ChoiceFilter(choices=QUALITY_CHOICES,lookup_expr='iexact',label='All Quality Category')
    categories = django_filters.ChoiceFilter(choices=PRODUCT_CATEGORY_CHOICES,lookup_expr='iexact',field_name='categories__name',label='All Category')

    reviews = django_filters.ChoiceFilter(choices = RATING_CHOICES,label= 'Product Rating', field_name='reviews__rating',lookup_expr='iexact')
    
    sizes = django_filters.ChoiceFilter(choices=PRODUCT_SIZE_CHOICES,lookup_expr='iexact', field_name='variant__size', label='Size')

    #anywhere you see field_name, it means that attribute is not direct attribute of the model (Product in hte is case) so you acess it through the related model (e.g sizes as a case study)
    
    
    class Meta:

        model = Products
        fields = ()