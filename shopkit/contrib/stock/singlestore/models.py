# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
from satchless.item import StockedItem


class VariantStockLevelMixin(models.Model, StockedItem):
    """
    Mixin for configurable Variant models with stock.

    Based on satchless.item.StockedItem, which requires get_stock method
    to be defined and checks quantity by calling check_quantity(self, quantity)
    method.

    Raises satchless.item.InsufficientStock exception by check_quantity
    if requested quantity less than variant's stock_level.
    """

    stock_level = models.PositiveIntegerField(
        _("stock level"), default=0,
        validators=[MinValueValidator(0), MaxValueValidator(999),])

    class Meta:
        abstract = True

    def get_stock(self):
        return self.stock_level


class OrderStockLevelMixin(models.Model):
    """
    Mixin for configurable Order models.

    Store stock substruction state, allow to call stock substruction
    via OrderedItem stock_handler and save self stock_state in db.
    """

    STOCK_FREE = 'not-taken-from-stock'
    STOCK_TAKEN = 'taken-from-stock'
    STOCK_STATE_CHOICES = (
        (STOCK_FREE, _('still in stock')),
        (STOCK_TAKEN, _('taken from stock')),
    )

    stock_state = models.CharField(
        _("stock state"), max_length=32,
        choices=STOCK_STATE_CHOICES, default=STOCK_FREE)

    class Meta:
        abstract = True

    def stock_handler(self, action=None, check_quantity=True):
        if action == 'take':
            if self.stock_state == self.STOCK_TAKEN:
                return True

            # check quantity if required
            if check_quantity and not self.check_lines_quantities():
                return False

            for group in self.groups.all():
                for line in group.lines.all():
                    line.stock_handler(action='take')

        elif action == 'free':
            if self.stock_state == self.STOCK_FREE:
                return True

            for group in self.groups.all():
                for line in group.lines.all():
                    line.stock_handler(action='free')

        else:
            return False

        self.stock_state = action
        self.save()

        return True


class OrderLineStockLevelMixin(models.Model):
    """
    Mixin for configurable OrderLine models

    Store substructed stock level in db and inform if missing items when
    stock_handler was called.
    Variant model should be inherited from StockedItem class.
    """

    stock_level_taken = models.PositiveIntegerField(
        _("stock level taken"), default=0,
        validators=[MinValueValidator(0), MaxValueValidator(999),])

    class Meta:
        abstract = True

    def stock_handler(self, action=None):
        """
        Stock level handler for OrderLine configurable class.

        Returns quantity_delta after taking of refunding values from stock.
        Negative quantity_delta means not all items was in stock when handler
        was called, it is possible only on "take" action.
        If None was returned, nothing was happend.
        """

        # should be called only from order
        quantity_delta = None
        stock_level = self.variant.get_stock()
        stock_level_taken = self.stock_level_taken

        if action == 'take':
            quantity_delta = stock_level - self.quantity
            if quantity_delta < 0:
                stock_level_taken = stock_level
                stock_level = 0
            else:
                stock_level_taken = self.quantity
                stock_level -= self.quantity

        elif action == 'free':
            quantity_delta = stock_level_taken
            stock_level += stock_level_taken
            stock_level_taken = 0

        else:
            return quantity_delta

        self.variant.stock_level = stock_level
        self.variant.save()

        self.stock_level_taken = stock_level_taken
        self.save()

        return quantity_delta
