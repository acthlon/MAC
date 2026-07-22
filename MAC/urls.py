"""
URL configuration for MAC project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
# from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                   SpectacularSwaggerView)

from core.views import HomePageAPIView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('materials/', include('materials.urls')),
    path('products/',include('products.urls')),
    path("api/",include("accounts.urls")),
    path('accounts/',include("allauth.urls")),
    path('review/',include('review.urls')), 
    path('cart/',include('cart.urls')),
    path('order/',include('order.urls')),
    path('checkout/', include('order.urls')),
    path('payments/',include('payments.urls')),
    path("",include("core.urls")),
       # 1. This generates the raw JSON/YAML file
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # 2. This creates the beautiful Swagger UI Website
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        # 3. (Optional) Redoc is just an alternative theme to Swagger
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

urlpatterns += static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)