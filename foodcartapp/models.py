from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
from django.db.models import Count


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже', 
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class Order(models.Model):
    STATUS_ORDER = [
        ('ACCEPTED', 'Принят'),
        ('PREPARING', 'Готовится'),
        ('DELIVERING', 'Передан курьеру'),
        ('DELIVERED', 'Доставлен'),
    ]
    PAYMENT_METHOD = [
        ('CASH', 'Наличными'),
        ('ONLINE', 'Электронно'),
    ]
    address = models.CharField(
        max_length=100,
        null=False,
        verbose_name='Адрес',
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=50,
        null=False,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=50,
        null=False,
    )
    phone_number = PhoneNumberField(
        region='RU',
        verbose_name='Мобильный номер',
        null=False,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_ORDER,
        default='ACCEPTED',
        verbose_name='Статус заказа',
        db_index=True,
    )
    comment = models.TextField(
        max_length=300,
        verbose_name='Комментарий к заказу',
        blank=True,
    )
    registered_at = models.DateTimeField(
        default=timezone.now,
        blank=True,
        verbose_name='Зарегистрирован в',
        db_index=True,
    )
    called_at = models.DateTimeField(
        blank=True,
        verbose_name='Звонок в',
        db_index=True,
        null=True,
    )
    delivered_at = models.DateTimeField(
        blank=True,
        verbose_name='Доставка в',
        db_index=True,
        null=True,
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD,
        db_index=True,
        verbose_name='Способ оплаты',
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Ресторан',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.address}"
    
    def get_suitable_restaurants(self):
        product_ids = self.items.values_list('product_id', flat=True)
        product_count = len(product_ids)
        
        restaurants = (
            Restaurant.objects
            .filter(menu_items__product_id__in=product_ids, menu_items__availability=True)
            .annotate(available_products=Count('menu_items__product_id', distinct=True))
            .filter(available_products=product_count)
            .distinct()
        )
        return restaurants


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='заказ',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='товар',
    )
    quantity = models.PositiveIntegerField(
        verbose_name='количество',
        validators=[MinValueValidator(1)],
    )
    price = models.DecimalField(
        verbose_name='цена при создании заказа',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = 'элемент заказа'
        verbose_name_plural = 'элементы заказов'

    def __str__(self):
        return f'{self.product}'
    