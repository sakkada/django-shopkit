# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from satchless.item import StockedItem


class VariantStockLevelMixin(StockedItem, models.Model):
    """Mixin for configurable Variant models with stock."""

    # Based on satchless.item.StockedItem, which requires get_stock method
    # to be defined and checks quantity by call check_quantity(self, quantity)
    # method. Raises satchless.item.InsufficientStock exception if requested
    # quantity less than variant's stock_level.

    sku = models.CharField(_('SKU'), max_length=128, db_index=True, unique=True,
                           help_text=_('ID of the product variant used'
                                       ' internally in the shop.'))
    stock_level = models.DecimalField(_("stock level"), max_digits=10,
                                      decimal_places=4, default=0)

    class Meta:
        abstract = True

    def get_stock(self):
        return self.stock_level
