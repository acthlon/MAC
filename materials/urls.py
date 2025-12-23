from django.urls import path,include
from materials.views import MaterialsView,MaterialDetailsView,MaterialUpdateView,MaterialDeleteView,MaterialCreateView


urlpatterns = [
    path('list/',MaterialsView.as_view(),name='material-list'),
    path('<slug:slug>/<uuid:pk>/',MaterialDetailsView.as_view(),name = 'material-details'),
    path('<slug:slug>/<uuid:pk>/update',MaterialUpdateView.as_view(),name='material-update'),
    path('<slug:slug>/<uuid:pk>/delete',MaterialDeleteView.as_view(),name='material-delete'),
    path('create/',MaterialCreateView.as_view(),name='material-create'),
]