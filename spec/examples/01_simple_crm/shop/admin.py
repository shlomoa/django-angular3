from django.contrib import admin

from .models import Customer, Product


class CustomerAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'active']
    list_editable = ['name', 'email', 'active']


class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'sku']
    list_editable = ['name', 'price']


admin.site.register(Customer, CustomerAdmin)
admin.site.register(Product, ProductAdmin)
