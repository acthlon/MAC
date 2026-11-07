import django_filters

from core.choices import ProductSize
from core.filters import CatalogItemFilter
from products.models import Products


class ProductFilter(CatalogItemFilter):
    sizes = django_filters.ChoiceFilter(
        choices=ProductSize.choices,
        lookup_expr="iexact",
        field_name="variant__size",
        label="Size",
    )
    # anywhere you see field_name, it means that attribute is not direct attribute of the model (Product in hte is case) so you acess it through the related model (e.g sizes as a case study)

    class Meta:
        model = Products
        fields = ()
