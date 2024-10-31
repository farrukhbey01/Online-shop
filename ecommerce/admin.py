from django.contrib import admin
from .models import Category, Product, Cart, CartItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')  # Ko'rsatmoqchi bo'lgan maydonlar
    search_fields = ('name',)  # Qidirish maydonlari
    ordering = ('name',)  # Saralash tartibi

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'stock', 'created_at', 'updated_at')
    search_fields = ('name', 'category__name')  # Kategoriyani qidirish uchun
    list_filter = ('category',)  # Filtr
    ordering = ('name',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at')
    search_fields = ('user__username',)  # Foydalanuvchini qidirish uchun
    ordering = ('-created_at',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'created_at', 'updated_at')
    search_fields = ('cart__user__username', 'product__name')  # Qidirish
    list_filter = ('cart', 'product')  # Filtr
    ordering = ('-created_at',)
