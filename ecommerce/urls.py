from django.urls import path
from .views import ProductViewSet, CartViewSet

urlpatterns = [
    path('products/', ProductViewSet.as_view({'get': 'list', 'post': 'create'}), name='product-list'),
    path('products/<int:pk>/', ProductViewSet.as_view({'put': 'update', 'delete': 'destroy'}), name='product-detail'),
    path('cart/', CartViewSet.as_view({'get': 'list'}), name='cart-list'),
    path('cart/add/', CartViewSet.as_view({'post': 'add_product'}), name='cart-add'),
    path('cart/remove/<int:pk>/', CartViewSet.as_view({'delete': 'remove_product'}), name='cart-remove'),
]