import random
from uuid import uuid4
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
from django_prices.models import PriceField
from satchless.item import InsufficientStock, ItemSet, ItemLine
from prices import Price

from ..utils import get_unique_uuid_string, countries
from . import signals


class DeliveryInfo(ItemLine):
    name = None
    price = None
    description = None

    def __init__(self, name, price, description):
        self.name = name
        self.price = price
        self.description = description

    def get_price_per_item(self, **kwargs):
        return self.price


class PaymentInfo(ItemLine):
    name = None
    price = None
    description = None

    def __init__(self, name, price, description):
        self.name = name
        self.price = price
        self.description = description

    def get_price_per_item(self, **kwargs):
        return self.price


class OrderStatus:
    CHECKOUT = 'checkout'
    PAYMENT_PENDING = 'payment-pending'
    PAYMENT_COMPLETE = 'payment-complete'
    PAYMENT_FAILED = 'payment-failed'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'

    CHOICES = (
        (CHECKOUT , _('undergoing checkout'),),
        (PAYMENT_PENDING, _('waiting for payment'),),
        (PAYMENT_COMPLETE, _('paid'),),
        (PAYMENT_FAILED, _('payment failed'),),
        (DELIVERED, _('shipped'),),
        (CANCELLED, _('cancelled'),),
    )


class Order(models.Model, ItemSet):
    SC = OrderStatus  # statuc container

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        on_delete=models.SET_NULL)
    cart = models.ForeignKey(
        'carts.Cart', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='orders')

    token = models.CharField(
        _('token'), max_length=36, unique=True, editable=False,
        default=get_unique_uuid_string)

    # Status value should not be set manually, .set_status() should be used.
    # To change choices or default value just redefine status field with new
    # SC instance (until django will provide a way to do it in more clean way).
    status = models.CharField(
        _('order status'), max_length=32,
        choices=SC.CHOICES, default=SC.CHECKOUT)
    status_history = models.TextField(editable=False, blank=True)

    billing_first_name = models.CharField(
        _("first name"), max_length=256, blank=True)
    billing_last_name = models.CharField(
        _("last name"), max_length=256, blank=True)
    billing_phone = models.CharField(
        _("phone number"), max_length=30, blank=True)
    billing_company_name = models.CharField(
        _("company name"), max_length=256, blank=True)

    billing_country = models.CharField(
        _("country"), max_length=2, blank=True,
        choices=countries.COUNTRY_CHOICES)
    billing_country_area = models.CharField(
        _("country administrative area"), max_length=256, blank=True)
    billing_city = models.CharField(_("city"), max_length=256, blank=True)
    billing_postal_code = models.CharField(
        _("postal code"), max_length=20, blank=True)

    billing_street_address_1 = models.CharField(
        _("street address 1"), max_length=256, blank=True)
    billing_street_address_2 = models.CharField(
        _("street address 2"), max_length=256, blank=True)

    payment_type = models.CharField(max_length=256, blank=True)
    payment_type_name = models.CharField(
        _('name'), max_length=128, blank=True, editable=False)
    payment_type_description = models.TextField(_('description'), blank=True)
    payment_price = PriceField(
        _('payment price'), currency=settings.SATCHLESS_DEFAULT_CURRENCY,
        max_digits=12, decimal_places=4, default=0, editable=False)

    date_create = models.DateTimeField(editable=False, auto_now_add=True)
    date_update = models.DateTimeField(editable=False, auto_now=True)
    date_last_status_change = models.DateTimeField(
        default=timezone.now, editable=False)

    class Meta:
        abstract = True
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ('-date_last_status_change',)

    def __iter__(self):
        for group in self.groups.all():
            yield group
        payment = self.get_payment()
        if payment:
            yield payment

    def __repr__(self):
        return '<Order #%d %s>' % (self.id, self.token,)

    def __unicode__(self):
        return u'Order (#%s, %s)' % (self.id, self.status,)

    def get_default_currency(self):
        return settings.SATCHLESS_DEFAULT_CURRENCY

    def set_status(self, new_status, failure=False):
        """
        Order new status setting handler.
        Extend method if required.

        New status value validity should be checked before save,
        if new value is incorrect, call this method with failure=True.
        On order.status changes should be placed after save, additionally,
        order_status_changed signal will be called if failure is False.
        See example's project orders.Order.set_status method for more details.
        """
        old_status = self.status
        self.status_history = '%s\n%s #%s %s: %s -> %s (%s)' % (
            self.status_history, timezone.now(),
            self.id, self.token, old_status, new_status,
            'successfull' if not failure else 'failure',
        )

        if not failure:
            self.status = new_status
            self.date_last_status_change = timezone.now()

        self.save()

        if not failure:
            signals.order_status_changed.send(sender=type(self), order=self,
                                              old_status=old_status)

        return failure

    def get_delivery_price(self):
        return sum([g.get_delivery().get_total() for g in self.groups.all()],
                   Price(0, currency=settings.SATCHLESS_DEFAULT_CURRENCY))

    def get_payment(self):
        return PaymentInfo(name=self.payment_type_name,
                           price=self.payment_price,
                           description=self.payment_type_description)

    def create_delivery_group(self, group):
        return self.groups.create(order=self,
                                  shipping_address_required=group.is_shipping)

    def is_empty(self):
        return not self.groups.filter(lines__isnull=False).exists()

    def check_lines_quantities(self):
        try:
            for group in self.groups.all():
                for line in group.lines.all():
                    if not line.quantity:
                        return False
                    line.variant.check_quantity(line.quantity)
        except InsufficientStock:
            return False
        return True

    def fix_lines_quantities(self):
        for group in self.groups.all():
            for item in group.lines.all():
                try:
                    if not item.quantity:
                        raise InsufficientStock(item.variant)
                    item.variant.check_quantity(item.quantity)
                except InsufficientStock:
                    if item.quantity:
                        item.quantity = item.variant.get_stock()
                    if item.quantity:
                        item.save()
                    else:
                        item.delete()

            if not group.lines.exists():
                group.delete()


class DeliveryGroup(models.Model, ItemSet):
    order = models.ForeignKey(
        'orders.Order', editable=False, on_delete=models.CASCADE,
        related_name='groups')

    delivery_type = models.CharField(
        _('delivery type'), max_length=256, blank=True)
    delivery_type_name = models.CharField(
        _('delivery name'), max_length=256, blank=True, editable=False)
    delivery_type_description = models.TextField(
        _('delivery description'), blank=True, editable=False)
    delivery_price = PriceField(
        _('delivery price'), default=0, editable=False,
        max_digits=12, decimal_places=4,
        currency=settings.SATCHLESS_DEFAULT_CURRENCY)

    shipping_address_required = models.BooleanField(
        default=False, editable=False)

    shipping_first_name = models.CharField(_("first name"), max_length=256)
    shipping_last_name = models.CharField(_("last name"), max_length=256)
    shipping_phone = models.CharField(
        _("phone number"), max_length=30, blank=True)
    shipping_company_name = models.CharField(
        _("company name"), max_length=256, blank=True)

    shipping_country = models.CharField(
        _("country"), max_length=2, blank=True,
        choices=countries.COUNTRY_CHOICES)
    shipping_country_area = models.CharField(
        _("country administrative area"), max_length=256, blank=True)
    shipping_city = models.CharField(_("city"), max_length=256)
    shipping_postal_code = models.CharField(_("postal code"), max_length=20)

    shipping_street_address_1 = models.CharField(
        _("street address 1"), max_length=256)
    shipping_street_address_2 = models.CharField(
        _("street address 2"), max_length=256, blank=True)

    date_create = models.DateTimeField(editable=False, auto_now_add=True)
    date_update = models.DateTimeField(editable=False, auto_now=True)

    class Meta:
        abstract = True

    def __iter__(self):
        for i in self.lines.all():
            yield i
        delivery = self.get_delivery()
        if delivery:
            yield delivery

    def get_default_currency(self):
        return settings.SATCHLESS_DEFAULT_CURRENCY

    def get_delivery(self):
        return DeliveryInfo(name=self.delivery_type_name,
                            price=self.delivery_price,
                            description=self.delivery_type_description)

    def create_order_line(self, variant, quantity, price, name=None):
        return self.lines.create(
            variant=variant, quantity=quantity, name=name or unicode(variant),
            unit_price_net=price.net, unit_price_gross=price.gross)


class OrderLine(models.Model, ItemLine):
    delivery_group = models.ForeignKey(
        'orders.DeliveryGroup', on_delete=models.CASCADE, related_name='lines')
    variant = models.ForeignKey(
        'products.Variant', blank=True, null=True, on_delete=models.SET_NULL)

    name = models.CharField(_('product with variant name'), max_length=256)

    quantity = models.PositiveIntegerField(
        _('quantity'), default=1,
        validators=[MinValueValidator(0), MaxValueValidator(999)])

    unit_price_net = models.DecimalField(
        _('unit price (net)'), max_digits=12, decimal_places=4)
    unit_price_gross = models.DecimalField(
        _('unit price (gross)'), max_digits=12, decimal_places=4)

    date_create = models.DateTimeField(editable=False, auto_now_add=True)
    date_update = models.DateTimeField(editable=False, auto_now=True)

    class Meta:
        abstract = True

    def get_price_per_item(self, **kwargs):
        return Price(net=self.unit_price_net, gross=self.unit_price_gross,
                     currency=self.delivery_group.get_default_currency())

    def get_quantity(self):
        return self.quantity
