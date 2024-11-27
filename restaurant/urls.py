from django.urls import path
from .views import Dashboard, OrderDetails,custom_login,custom_signup


urlpatterns = [
    path('login/',custom_login, name='custom_login'),
    path('signup/', custom_signup, name='custom_signup'),
    path('dashboard/', Dashboard.as_view(), name='dashboard'),
    path('orders/<int:pk>/', OrderDetails.as_view(), name='order-details'),
]
