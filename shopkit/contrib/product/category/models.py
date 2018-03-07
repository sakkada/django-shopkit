from django.urls import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel


__all__ = ('Category', 'CategorizedProductMixin')


class Category(MPTTModel):
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children',
        on_delete=models.CASCADE)

    name = models.CharField(_('name'), max_length=128)
    description = models.TextField(_('description'), blank=True)
    meta_description = models.TextField(
        _('meta description'), blank=True,
        help_text=_('Description used by search and indexing engines'))
    slug = models.SlugField(max_length=50)

    class Meta:
        abstract = True
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product:category-details', kwargs={
            'parent_slugs': self.parents_slug_path(),
            'category_slug': self.slug,
        })

    def parents_slug_path(self):
        parents = '/'.join(c.slug for c in self.get_ancestors())
        return '%s/' % parents if parents else ''


class CategorizedProductMixin(models.Model):
    categories = models.ManyToManyField(
        'products.Category', related_name='products')

    class Meta:
        abstract = True

    def get_categories(self):
        return self.categories.all()

    def get_absolute_url(self, category=None):
        if category or self.get_categories().exists():
            if not category:
                category = self.categories.all()[0]
            args = ('%s%s/' % (category.parents_slug_path(), category.slug),
                    self.pk,)
            return reverse('product:details', args=args)
        return super(CategorizedProductMixin, self).get_absolute_url()
