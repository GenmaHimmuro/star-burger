from django.contrib import admin

from .models import Place

@admin.register(Place)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'address',
        'lat',
        'lon',
    ]
