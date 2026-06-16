from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]


class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.FloatField()
    sku = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["id"]
