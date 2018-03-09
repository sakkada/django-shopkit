from django.apps import AppConfig


class OrdersConfig(AppConfig):
    label = u'orders'
    name = u'shop.orders'
    verbose_name = u'Orders'

    def ready(self):
        from . import listeners
        listeners.start_listening()
