from django.apps import AppConfig


class CartsConfig(AppConfig):
    label = u'carts'
    name = u'shop.carts'
    verbose_name = u'Carts'

    def ready(self):
        from . import listeners
        listeners.start_listening()
