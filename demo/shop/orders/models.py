from django.db import models
import shopkit.order.models


class Order(shopkit.order.models.Order):
    pass


class DeliveryGroup(shopkit.order.models.DeliveryGroup):
    order = models.ForeignKey(Order, related_name='groups', editable=False)


class OrderedItem(shopkit.order.models.OrderedItem):
    delivery_group = models.ForeignKey(DeliveryGroup, related_name='items',
                                       editable=False)
    product_variant = models.ForeignKey('product.Variant', related_name='+',
                                        null=True, blank=True,
                                        on_delete=models.SET_NULL)
