# -*- coding:utf-8 -*-
import decimal
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django_prices.models import PriceField
from prices import FractionalDiscount, LinearTax
from shopkit.product import models as productmodels
from shopkit.contrib.product.category import models as catmodels
from shopkit.contrib.stock.singlestore import models as stockmodels


class Category(catmodels.Category):
    pass


class Discount(FractionalDiscount, models.Model):
    name = models.CharField(_('internal name'), max_length=100)
    rate = models.DecimalField(
        _('rate'), max_digits=4, decimal_places=2,
        help_text=_('Percentile rate of the discount.'))
    rate_name = models.CharField(
        _('display name'), max_length=30,
        help_text=_(u'Name of the rate which will be displayed to the user.'))

    def __init__(self, *args, **kwargs):
        # ignore FractionalDiscount's __init__
        return super(FractionalDiscount, self).__init__(*args, **kwargs)

    @property
    def factor(self):
        return decimal.Decimal(self.rate) / 100

    @factor.setter
    def factor(self, value):
        pass

    def __unicode__(self):
        return self.rate_name


class Tax(models.Model):
    name = models.CharField(_('group name'), max_length=100)
    rate = models.DecimalField(
        _('rate'), max_digits=4, decimal_places=2,
        help_text=_('Percentile rate of the tax.'))
    rate_name = models.CharField(
        _('name of the rate'), max_length=30,
        help_text=_('Name of the rate which will be displayed to the user.'))

    class Meta:
        verbose_name = _('Tax')
        verbose_name_plural = _('Taxes')

    def __unicode__(self):
        return self.name

    def get_tax(self):
        return LinearTax(self.rate * decimal.Decimal('0.01'), self.rate_name)


class Maker(models.Model):
    name = models.CharField(_('manufacturer'), max_length=256)

    class Meta:
        verbose_name = _('Maker')
        verbose_name_plural = _('Makers')

    def __unicode__(self):
        return self.name


class Product(catmodels.CategorizedProductMixin,
              productmodels.Product):

    QTY_MODE_CHOICES = (
        ('product', _('per product'),),
        ('variant', _('per variant'),),
    )

    discount = models.ForeignKey(
        Discount, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='products')
    tax = models.ForeignKey(
        Tax, null=True, blank=True, on_delete=models.SET_NULL)
    maker = models.ForeignKey(
        Maker, null=True, blank=True, on_delete=models.SET_NULL,
        help_text=_('Product manufacturer'))

    name = models.CharField(_('name'), max_length=256)
    description = models.TextField(_('description'), blank=True)

    price = PriceField(
        _('base price'), currency='EUR', max_digits=12, decimal_places=4)

    qty_mode = models.CharField(
        _('Quantity pricing mode'), max_length=10,
        choices=QTY_MODE_CHOICES, default='variant', help_text=_(
            "In 'per variant' mode the unit price will depend on quantity"
            " of single variant being sold. In 'per product' mode, total"
            " quantity of all product's variants will be used."
        ))

    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')

    def __unicode__(self):
        return self.name

    def get_product_base_price(self, quantity):
        overrides = self.qty_price_overrides.all()
        overrides = overrides.filter(min_qty__lte=quantity).order_by('-min_qty')
        try:
            return overrides[0].price
        except Exception:
            return self.price


class Variant(stockmodels.VariantStockLevelMixin,
              productmodels.Variant):
    price_offset = PriceField(_('unit price offset'), currency='EUR',
                              default=0, max_digits=12, decimal_places=4)

    SIZE_CHOICES = [
        ('XS', 'XS',),
        ('S', 'S',),
        ('M', 'M',),
        ('L', 'L',),
        ('XL', 'XL',),
    ]
    size = models.CharField(choices=SIZE_CHOICES, max_length=2)

    COLOR_CHOICES = [
        ('red', _('Red'),),
        ('green', _('Green'),),
        ('blue', _('Blue'),),
    ]
    color = models.CharField(max_length=32, choices=COLOR_CHOICES)

    class Meta:
        verbose_name = _('Variant')
        verbose_name_plural = _('Variants')

    def get_price_per_item(self, discount=True, quantity=1, **kwargs):
        price = self.product.get_product_base_price(quantity=quantity)
        price += self.price_offset
        if discount and self.product.discount:
            price += self.product.discount
        return price

    def get_price(self, **kwargs):
        price = super(Variant, self).get_price(**kwargs)
        if self.product.tax:
            price += self.product.tax.get_tax()
        return price


class PriceQtyOverride(models.Model):
    """
    Overrides price of product unit, depending of total quantity being sold.
    """
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='qty_price_overrides')

    min_qty = models.DecimalField(
        _('minimal quantity'), max_digits=10, decimal_places=4)
    price = PriceField(
        _('unit price'), currency=settings.SATCHLESS_DEFAULT_CURRENCY,
        max_digits=12, decimal_places=4)

    class Meta:
        ordering = ('min_qty',)
