from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import user_passes_test
from django.db.models import F, Sum
from django.contrib.auth import authenticate, login, views as auth_views
from geopy import distance

from foodcartapp.models import Product, Restaurant, Order
from place_coord.get_coord import get_all_coordinates


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = (
        Order.objects.exclude(status='DELIVERED')
        .annotate(total_cost=Sum(F('items__price') * F('items__quantity')))
        .order_by('-id')
        .prefetch_related('items', 'items__product')
        .select_related('restaurant')
        .with_suitable_restaurants()
    )

    addresses = (
        {order.address for order in orders} |
        {order.restaurant.address for order in orders if order.restaurant} |
        {r.address for order in orders for r in order.suitable_restaurants}
    )

    coords_map = get_all_coordinates(addresses)

    for order in orders:
        order.selected_restaurant = order.restaurant
        order.selected_restaurant_distance = None
        order.order_address_error = None

        order_coords = coords_map.get(order.address)
        if not order_coords:
            order.order_address_error = "Адрес не найден"
            order.suitable_restaurants_with_distance = []
            continue

        if order.restaurant and (rest_coords := coords_map.get(order.restaurant.address)):
            order.selected_restaurant_distance = round(
                distance.distance(order_coords, rest_coords).km, 3
            )

        suitable = [
            rest for rest in order.suitable_restaurants
            if not order.restaurant or rest.id != order.restaurant.id
        ]

        suitable_with_distance = []
        for rest in suitable:
            r_coords = coords_map.get(rest.address)
            dist = round(distance.distance(order_coords, r_coords).km, 3) if r_coords else None
            suitable_with_distance.append({
                'restaurant': rest,
                'distance': dist
            })

        suitable_with_distance.sort(
            key=lambda x: x['distance'] if x['distance'] is not None else float('inf')
        )

        order.suitable_restaurants_with_distance = suitable_with_distance

    return render(request, 'order_items.html', {'order_items': orders})
