from django.urls import path

from .models import Category
from .views import ProductViewSet, CartViewSet,PaymentViewSet,CategoryViewSet

urlpatterns = [
    path('products/<int:category_id>/', ProductViewSet.as_view({'patch': 'destroy'}), name='destroy_products'),
    path('category/',CategoryViewSet.as_view({'get':'list','post':'create'})),
    path('products/', ProductViewSet.as_view({ 'post': 'create','get':'list'}), name='product-list'),
    # path('products/<int:pk>/', ProductViewSet.as_view({'put': 'update', 'delete}), name='product-detail'),
    path('cart/', CartViewSet.as_view({'get': 'list'}), name='cart-list'),
    path('cart/add/', CartViewSet.as_view({'post': 'add_product'}), name='cart-add'),
    path('cart/update_remove/', CartViewSet.as_view({'patch': 'update_or_remove_product'}), name='cart-remove'),
    path('payments/', PaymentViewSet.as_view({'post': 'create'}), name='payment-list'),
    # To‘lov yaratish va ro‘yxatini olish
    # path('payments/<int:id>/', PaymentViewSet.as_view({'get': 'retrieve'}), name='payment-detail'),
    # Ma'lum to‘lov haqida ma'lumot olish
]