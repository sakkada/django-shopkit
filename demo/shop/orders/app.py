import shopkit.order.app
from . import models


class OrderApp(shopkit.order.app.OrderApp):
    Order = models.Order
    DeliveryGroup = models.DeliveryGroup
    OrderedItem = models.OrderedItem
    
