"""
Stock hangling support example for shopkit store.

To install this example do the following:
Inherit Variant model from VariantStockLevelMixin:

    class Variant(stockmodels.VariantStockLevelMixin, models.Variant):

Inherit Order and OrderLine models from respective OrderStockLevelMixin and
OrderLineStockLevelMixin and somewhere in set_status use stock_handler to
take and refund items from stock:

    from shopkit.order import models
    from shopkit.contrib.stock.singlestore import models as stockmodels


    class Order(stockmodels.OrderStockLevelMixin, models.Order):
        def set_status(self, new_status, failure=False):
            super(Order, self).set_status(new_status, failure=failure)

            if some_condition:
                self.stock_handler(action='take')
            if another_condition:
                self.stock_handler(action='free')

            return True


    class OrderLine(stockmodels.OrderLineStockLevelMixin, models.OrderLine):
        pass

Full code see in example project.
"""
