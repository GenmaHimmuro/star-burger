from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.response import Response
from rest_framework.decorators import api_view
import json


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
@api_view(['GET'])
def register_order(request):
    json_data = request.data
    products = json_data.get('products')
    first_name = json_data.get('firstname')
    last_name = json_data.get('lastname')
    address = json_data.get('address')
    phone_number = json_data.get('phonenumber')

    order = Order(
        first_name=first_name,
        last_name=last_name,
        address=address,
        phone_number=phone_number,
    )
    order.save()

    for product in products:
        OrderItem.objects.create(
            order_id=order.id,
            product_id=product.get('product'),
            quantity=product.get('quantity'),
        )
    return Response()
