from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import serializers
from rest_framework import status
from django.db import transaction

from .models import Product
from .models import Order
from .models import OrderItem


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
@transaction.atomic
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    if serializer.is_valid():
        order = Order(
            first_name=serializer.validated_data['firstname'],
            last_name=serializer.validated_data['lastname'],
            address=serializer.validated_data['address'],
            phone_number=serializer.validated_data['phonenumber'],
        )
        order.save()

        for product_data in serializer.validated_data['products']:
            product = Product.objects.get(id=product_data['product'])
            OrderItem.objects.create(
                order=order,
                product_id=product,
                quantity=product_data['quantity'],
                price=product.price,
            )
        return Response(
            OrderResponseSerializer(order).data,
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderSerializer(serializers.Serializer):
    products = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
        error_messages={
            'required': 'products: Обязательное поле',
            'empty': 'products: Этот список не может быть пустым',
        },
        write_only=True
    )
    firstname = serializers.CharField(
        required=True,
        error_messages={'required': 'first_name: Обязательное поле'}
    )
    lastname = serializers.CharField(
        required=True,
        error_messages={'required': 'last_name: Обязательное поле'}
    )
    phonenumber = serializers.CharField(
        required=True,
        error_messages={'required': 'phone_number: Обязательное поле'}
    )
    address = serializers.CharField(
        required=True,
        error_messages={'required': 'address: Обязательное поле'}
    )


class OrderResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'address']
