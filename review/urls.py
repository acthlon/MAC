from django.urls import path
from review.views import ReviewListView,ReviewCreateView,ReviewListByItem,ReviewDeleteView,ReviewUpdateView


# NOTE: GIVE THES ENPOINTS BETTER NAME, FOLLOW THE REST APPROACH
urlpatterns = [
    path('<str:model_name>/<slug:slug>/<uuid:pk>/create/',ReviewCreateView.as_view(), name='review-create'),
    path('<str:pk>/update/',ReviewUpdateView.as_view(), name='review-update'),
    path('<str:pk>/delete/',ReviewDeleteView.as_view(), name='review-delete'),
    path('all-reviews/',ReviewListView.as_view(), name='reviews'),
    path('<str:model_name>/<slug:slug>/<uuid:pk>/all/',ReviewListByItem.as_view(),name='single-item-review'),
]