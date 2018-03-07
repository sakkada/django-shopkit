from shopkit.order import models
from shopkit.contrib.stock.singlestore import models as stockmodels


class Order(stockmodels.OrderStockLevelMixin, models.Order):

    def set_status(self, new_status, failure=False):
        """Order new status setting extended handler."""

        old_status, SC = self.status, self.SC

        # check possibility of new_status value setting
        if old_status == new_status:
            failure = True
        if old_status == SC.PAYMENT_PENDING and new_status == SC.CHECKOUT:
            failure = True

        # save new_status and call signal
        super(Order, self).set_status(new_status, failure=failure)
        if not failure:
            return failure

        # do some on change status staff
        if new_status == SC.PAYMENT_COMPLETE and old_status == SC.PAYMENT_PENDING:
            self.stock_handler(action='take')
        if new_status == SC.CANCELLED and old_status == SC.PAYMENT_COMPLETE:
            self.stock_handler(action='free')

        # sending email message on status changed here
        email_template = new_status

        return failure


class DeliveryGroup(models.DeliveryGroup):
    pass


class OrderLine(stockmodels.OrderLineStockLevelMixin, models.OrderLine):
    pass
