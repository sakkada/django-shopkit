from django.conf.urls import url
from shopkit.order import app
from . import models


class OrderApp(app.OrderApp):
    Order = models.Order
    DeliveryGroup = models.DeliveryGroup
    OrderLine = models.OrderLine

    # Views methods section
    # ---------------------
    def get_urls(self):
        return [
            url(r'^$', self.index, name='index'),
            url(r'^(?P<order_token>[0-9a-zA-Z]+)/$', self.details,
                name='details'),
        ]
