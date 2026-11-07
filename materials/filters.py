from core.filters import CatalogItemFilter
from materials.models import Materials


class MaterialsFilter(CatalogItemFilter):
    class Meta:
        model = Materials
        fields = ()
