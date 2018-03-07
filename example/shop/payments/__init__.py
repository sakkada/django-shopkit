# -*- coding:utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from shopkit.payment import PaymentProvider, PaymentType


class SimplePaymentProvider(PaymentProvider):
    typ = 'simple_payment'
    name = _('Simple cash payment.')

    def __init__(self, *args, **kwargs):
        super(SimplePaymentProvider, self).__init__(*args, **kwargs)

    def enum_types(self, order=None, customer=None):
        yield PaymentType(provider=self, typ=self.typ, name=self.name)

    def save(self, order, form, typ=None):
        order.payment_price = 0
        order.payment_type_name = self.name
        order.payment_type_description = self.name

    def confirm(self, order, typ=None):
        return
