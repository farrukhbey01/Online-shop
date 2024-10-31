from django.urls import path

from .models import Category
from .views import ProductViewSet, CartViewSet,PaymentViewSet,CategoryViewSet

urlpatterns = [
    path('products/<int:category_id>/', ProductViewSet.as_view({'patch': 'destroy'}), name='destroy_products'),
    path('category/',CategoryViewSet.as_view({'get':'list','post':'create'})),
    path('products/', ProductViewSet.as_view({ 'post': 'create','get':'list'}), name='product-list'),
    path('cart/update_remove/', CartViewSet.as_view({'patch': 'update_or_remove_product'}), name='cart-remove'),
    path('payments/', PaymentViewSet.as_view({'post': 'create'}), name='payment-list'),


]