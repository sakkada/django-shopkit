from django.db import models


class CartLineQuerySet(models.QuerySet):
    def active(self):
        return self


class CartLineManager(models.Manager):
    queryset_class = CartLineQuerySet

    def get_queryset(self):
        return self.queryset_class(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()
