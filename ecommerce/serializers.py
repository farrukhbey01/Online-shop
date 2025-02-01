from rest_framework import serializers
from .models import Category, Product, CartItem, Cart
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'user', 'amount', 'payment_method', 'status', 'created_at']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock']


class ProductCreateSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    products = ProductSerializer(many=True)

    def validate_category_id(self, value):
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("Category not found.")
        return value

    def create(self, validated_data):
        category_id = validated_data['category_id']
        products_data = validated_data['products']


        category = Category.objects.get(id=category_id)

        products = [Product(category=category, **product_data) for product_data in products_data]
        return Product.objects.bulk_create(products)

class ProductCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price']

class ProductDestroySerializer(serializers.Serializer):
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductCartSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cartitem_set', many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items']

class CartListSerializer(serializers.ModelSerializer):
    products = CartItemSerializer(source='cartitem_set', many=True)
    total_items = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'products', 'total_items', 'total_price']
