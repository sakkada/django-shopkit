# -*- coding: utf-8 -*-
from uuid import uuid4
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
from jsonfield import JSONField
from satchless.item import ItemSet, ItemLine, InsufficientStock
from ..utils import get_unique_uuid_string
from . import signals


class Cart(models.Model, ItemSet):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        related_name='carts', on_delete=models.CASCADE)

    token = models.CharField(
        _('token'), max_length=36, unique=True, editable=False,
        default=get_unique_uuid_string)

    class Meta:
        abstract = True

    def __repr__(self):
        return 'Cart(user=%s, token=%s)' % (self.user, self.token,)

    def __iter__(self):
        for i in self.lines.all():
            yield i

    def __len__(self):
        return self.lines.count()

    def __nonzero__(self):
        return True  # need to set cart as True object if __len__ is zero

    def get_currency(self, **kwargs):
        return settings.SATCHLESS_DEFAULT_CURRENCY

    def get_line(self, variant, data=None):
        """Return a line matching the given variant and data."""
        if data is None:
            data = {}
        lines = self.lines.filter(variant=variant)
        lines = [line for line in lines if line.data == data]
        return lines[0] if lines else None

    def is_empty(self):
        return not self.lines.exists()

    def check_lines_quantities(self):
        try:
            for line in self.lines.all():
                if not line.quantity:
                    return False
                line.variant.check_quantity(line.quantity)
        except InsufficientStock:
            return False
        return True

    def fix_lines_quantities(self):
        for line in self.lines.all():
            try:
                line.variant.check_quantity(line.quantity)
            except InsufficientStock:
                self.add(line.variant, quantity=line.variant.get_stock(),
                         data=line.data, replace=True, check_quantity=True)

    def add(self, variant, quantity=1, data=None, replace=False,
            check_quantity=True):
        """
        Add a product vartiant to cart.
        The `data` parameter may be used to differentiate between items with
        different customization options.
        If `replace` is truthy then any previous quantity is discarded instead
        of added to.
        """
        # todo: do nothing if quantity is zero and cart_line does not exists

        if not self.pk:
            self.save()  # just try to prevent saving on get from request

        cart_line, _ = self.lines.get_or_create(
            variant=variant, defaults={'quantity': 0, 'data': data or {},})

        new_quantity = quantity if replace else cart_line.quantity + quantity
        if new_quantity < 0:
            raise ValueError('%r is not a valid quantity (results in %r)' % (
                quantity, new_quantity))

        if check_quantity:
            variant.check_quantity(new_quantity)

        cart_line.quantity = new_quantity

        if not cart_line.quantity:
            cart_line.delete()
        else:
            cart_line.save(update_fields=['quantity'])

        signals.cart_line_changed.send(sender=type(self),
                                       cart=self, cart_line=cart_line)

        return cart_line


class CartLine(models.Model, ItemLine):
    cart = models.ForeignKey(
        'carts.Cart', editable=False, on_delete=models.CASCADE,
        related_name='lines')
    variant = models.ForeignKey('products.Variant', on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(
        _('quantity'), default=1,
        validators=[MinValueValidator(0), MaxValueValidator(999),])
    data = JSONField(blank=True, default={})

    class Meta:
        unique_together = ('cart', 'variant', 'data',)
        abstract = True

    def __unicode__(self):
        return u"%s × %d" % (self.variant, self.quantity,)

    def __repr__(self):
        return 'CartLine(variant=%r, quantity=%r, data=%r)' % (
            self.variant, self.quantity, self.data)

    def __eq__(self, other):
        if not isinstance(other, CartLine):
            return NotImplemented

        return (self.product == other.product and
                self.quantity == other.quantity and
                self.data == other.data)

    def __ne__(self, other):
        return not self == other

    def __getstate__(self):
        return self.variant, self.quantity, self.data

    def __setstate__(self, data):
        self.variant, self.quantity, self.data = data

    def get_price_per_item(self, **kwargs):
        return self.variant.get_price(**kwargs)

    def get_quantity(self, **kwargs):
        return self.quantity
