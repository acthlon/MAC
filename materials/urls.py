from django.urls import path,include
from materials.views import MaterialsListView,MaterialDetailsView,MaterialUpdateView,MaterialDeleteView,MaterialCreateView


urlpatterns = [
    path('list/',MaterialsListView.as_view(),name='material_list'),
    path('<slug:slug>/<uuid:pk>/',MaterialDetailsView.as_view(),name = 'material_details'),
    path('<slug:slug>/<uuid:pk>/update/',MaterialUpdateView.as_view(),name='material_update'),
    path('<slug:slug>/<uuid:pk>/delete/',MaterialDeleteView.as_view(),name='material_delete'),
    path('create/',MaterialCreateView.as_view(),name='material_create'),
]

