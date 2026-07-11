from django.urls import path,include
from materials.views import MaterialsListView,MaterialDetailsView,MaterialUpdateView,MaterialDeleteView,MaterialCreateView


# NOTE: HMMMMMMMMM, THIS NAMING GET AS E BE OOOOO

urlpatterns = [
    path('list/',MaterialsListView.as_view(),name='material_list'),
    path('<slug:slug>/<uuid:pk>/',MaterialDetailsView.as_view(),name = 'material-details'),
    path('<slug:slug>/<uuid:pk>/update/',MaterialUpdateView.as_view(),name='material-update'),
    path('<slug:slug>/<uuid:pk>/delete/',MaterialDeleteView.as_view(),name='material-delete'),
    path('create/',MaterialCreateView.as_view(),name='material-create'),
]

