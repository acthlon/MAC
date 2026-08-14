from django.urls import path

from materials.views import (
    MaterialCreateView,
    MaterialDetailView,
    MaterialsListView,
    MaterialUpdateDeleteView,
)

urlpatterns = [
    path("create/", MaterialCreateView.as_view(), name="material_create"),
    path(
        "<slug:slug>/<uuid:pk>/", MaterialDetailView.as_view(), name="material_details"
    ),
    path(
        "<slug:slug>/<uuid:pk>/manage/",
        MaterialUpdateDeleteView.as_view(),
        name="material_update_delete",
    ),
    path("", MaterialsListView.as_view(), name="material_list"),
]
