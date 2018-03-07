from django.apps import AppConfig


class OrdersConfig(AppConfig):
    label = u'orders'
    name = u'shop.orders'
    verbose_name = u'Orders'

    def ready(self):
        pass
