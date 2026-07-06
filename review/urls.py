from django.urls import path
from review.views import ReviewListView,ReviewCreateView,ReviewListByItem,ReviewDeleteView,ReviewUpdateView


urlpatterns = [
    path('<str:model_name>/<slug:slug>/<uuid:pk>/create/',ReviewCreateView.as_view(), name='review_create'),
    path('<str:pk>/update/',ReviewUpdateView.as_view(), name='review_update'),
    path('<str:pk>/delete/',ReviewDeleteView.as_view(), name='review_delete'),
    path('all-reviews/',ReviewListView.as_view(), name='reviews'),
    path('<str:model_name>/<slug:slug>/<uuid:pk>/all/',ReviewListByItem.as_view(),name='all_single_item_review'),
]