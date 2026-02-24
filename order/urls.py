from django.urls import path
from order.views import CheckoutPreviewAPIView,AddressView,OrderListView,OrderDetailsView,CheckoutPreviewAPIView,CreateOrderFromCartView,InitializePaymentAPIView,PaymentCallbackAPIView,CreateOrderFromCartView

urlpatterns = [
    path('preview/',CheckoutPreviewAPIView.as_view(), name='cart-preview'),
    path('address/create/', AddressView.as_view(), name = 'address-create'),
    path('address/<uuid:pk>/update/', AddressView.as_view(),name='address-update'),
    path('place_order/', CreateOrderFromCartView.as_view(), name='place-order'),
    path('lists/',OrderListView.as_view(),name='order-list'),
    path('<uuid:pk>/',OrderDetailsView.as_view(),name='order-details'),
    path('<uuid:pk>/initialize_payment/',InitializePaymentAPIView.as_view(),name='initialize-payment'
),path('payment_callback/',PaymentCallbackAPIView.as_view(),name='payment-callback')
]