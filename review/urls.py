from django.urls import path

from review.views import (
    ReviewCreateView,
    ReviewListByItem,
    ReviewUpdateDeleteView,
)

urlpatterns = [
    path(
        "<str:model_name>/<slug:slug>/<uuid:pk>/create/",
        ReviewCreateView.as_view(),
        name="review_create",
    ),
    path(
        "<str:pk>/manage/",
        ReviewUpdateDeleteView.as_view(),
        name="review_update_delete",
    ),
    path(
        "<str:model_name>/<slug:slug>/<uuid:pk>/all/",
        ReviewListByItem.as_view(),
        name="all_single_item_review",
    ),
]
