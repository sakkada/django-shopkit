# -*- coding:utf-8 -*-
from shopkit.payment import PaymentProvider, PaymentType


class CashPaymentProvider(PaymentProvider):
    typ = u'cash_payment'

    select_name = {
        u'getfromshop_delivery': u'Оплата наличными или банковской'
                                 u' картой при получении заказа',
        u'dpd_terminal_terminal_type': u'Оплата наличными при'
                                       u' получении товара',
        u'dpd_terminal_door_type': u'Оплата наличными при получении товара',
    }

    name = select_name['getfromshop_delivery']

    def __init__(self, *args, **kwargs):
        super(CashPaymentProvider, self).__init__(*args, **kwargs)

    def enum_types(self, order=None, customer=None):
        delivery_group = order.groups.all()[0]

        if delivery_group.delivery_type in self.select_name:
            self.name = self.select_name[delivery_group.delivery_type]

        yield PaymentType(provider=self, typ=self.typ, name=self.name)

    def save(self, order, form, typ=None):
        order.payment_price = 0
        order.payment_type_name = self.name
        order.payment_type_description = self.name

    def confirm(self, order, typ=None):
        return
