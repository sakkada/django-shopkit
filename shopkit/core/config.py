from django.apps import AppConfig


class CoreConfig(AppConfig):
    label = u'shopkit.core'
    name = u'shopkit.core'
    verbose_name = u'Shopkit Core'

    def ready(self):
       pass
