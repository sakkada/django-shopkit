from django.db import models
from django.utils.translation import ugettext_lazy as _
import decimal

from ..item import ItemRange, Item
from ..utils.models import Subtyped, DeferredField

__all__ = ('Product', 'Variant')


class Product(Subtyped, ItemRange):
    """
    Django binding for a product group (product with multiple variants)
    """

    quantity_quantizer = decimal.Decimal(1)
    quantity_rounding = decimal.ROUND_HALF_UP

    class Meta:
        abstract = True

    def __repr__(self):
        return '<Product #%r>' % self.pk

    def __iter__(self):
        return iter(self.variants.all())

    @models.permalink
    def get_absolute_url(self):
        return 'product:details', (self.pk,)

    def quantize_quantity(self, quantity):
        """
        Returns sanitized quantity. By default it rounds the value to the
        nearest integer.
        """
        return decimal.Decimal(quantity).quantize(
            self.quantity_quantizer, rounding=self.quantity_rounding)


class Variant(Subtyped, Item):
    """
    Django binding for a single variant of product
    """
    class Meta:
        abstract = True

    def __repr__(self):
        return '<Variant #%r>' % (self.id,)
