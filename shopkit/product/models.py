from django.db import models
from django.urls import reverse
from satchless.item import ItemRange, Item


__all__ = ('Product', 'Variant')


class Product(models.Model, ItemRange):
    """Django binding for a product group (product with multiple variants)."""

    class Meta:
        abstract = True

    def __repr__(self):
        return '<Product #%d>' % self.pk

    def __iter__(self):
        return iter(self.variants.all())

    def get_absolute_url(self):
        return reverse('product:details', kwargs={'product_pk': self.pk,})


class Variant(models.Model, Item):
    """Django binding for a single variant of product."""

    product = models.ForeignKey(
        'products.Product', related_name='variants', on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def __repr__(self):
        return '<Variant #%d>' % self.id
