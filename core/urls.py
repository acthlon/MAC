from django.urls import path

from core.views import HomePageAPIView

urlpatterns = [path("", HomePageAPIView.as_view(), name="home")]
