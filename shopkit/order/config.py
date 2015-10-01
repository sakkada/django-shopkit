from django.apps import AppConfig


class ProductsConfig(AppConfig):
    label = u'products'
    name = u'shop.products'
    verbose_name = u'Products'

    def ready(self):
        from . import forms
