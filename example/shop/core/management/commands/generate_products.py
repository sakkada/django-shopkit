# -- coding: utf-8 --
import sys
from django.core.management.base import BaseCommand
from random import randrange, randint
from shop.products import models


class Command(BaseCommand):
    def handle(self, *args, **options):
        index = {
            'discount': models.Discount,
            'categories': models.Category,
            'tax': models.Tax,
            'maker': models.Maker,
        }
        values = {k: list(v.objects.all()) for k, v in index.items()}
        choices = {
            'color': models.Variant.COLOR_CHOICES,
            'size': models.Variant.SIZE_CHOICES,
        }

        sys.stdout.write('Generating products: ')
        for i in range(500):
            sys.stdout.write('.')
            fk = {k: v[randrange(len(v))] for k, v in values.items()
                  if k not in ['categories',]}
            fk['price'] = randint(100, 10000)
            mm = {k: v[randrange(len(v))] for k, v in values.items()
                  if k in ['categories',]}
            p = models.Product(name='Product #%s' % i, **fk)
            p.save()
            for k, v in mm.items():
                getattr(p, k).set([v])

            for i in range(1, randrange(2, 10)):
                v = models.Variant(
                    product=p,
                    price_offset=randrange(0, 1000),
                    # sku='PV-%s-%s' % (p.id, i,),
                    stock_level=randrange(0, 10),
                    color=models.Variant.COLOR_CHOICES[
                        randrange(len(models.Variant.COLOR_CHOICES))
                    ][0],
                    size=models.Variant.SIZE_CHOICES[
                        randrange(len(models.Variant.SIZE_CHOICES))
                    ][0],
                )
                v.save()
        sys.stdout.write('finished.')
