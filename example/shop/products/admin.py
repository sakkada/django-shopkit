# -*- coding:utf-8 -*-
from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from mptt.admin import MPTTModelAdmin
from . import models


# Admin forms
# -----------
class CategoryMixin:
    def label_from_instance(self, obj):
        level = getattr(obj, obj._mptt_meta.level_attr)
        return u'%s%s' % ('. ' * level, unicode(obj))


class CategoryChoiceField(CategoryMixin, forms.ModelChoiceField):
    pass


class CategoryMultipleChoiceField(CategoryMixin, forms.ModelMultipleChoiceField):
    pass


class CategoryForm(forms.ModelForm):
    class Meta:
        model = models.Category
        fields = ('name', 'slug', 'parent', 'description', 'meta_description',)

    parent = CategoryChoiceField(
        queryset=models.Category.objects.order_by('tree_id', 'lft'),
        required=False)

    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['parent'].queryset = models.Category.objects.exclude(
                tree_id=self.instance.tree_id,
                lft__gte=self.instance.lft, rght__lte=self.instance.rght
            ).order_by('tree_id', 'lft')


class ProductForm(forms.ModelForm):
    categories = CategoryMultipleChoiceField(
        required=False,
        queryset=models.Category.objects.order_by('tree_id', 'lft'))

    class Meta:
        model = models.Product
        fields = '__all__'


# Model admins
# ------------
class CategoryAdmin(MPTTModelAdmin):
    form = CategoryForm
    prepopulated_fields = {'slug': ('name',),}


class DiscountAdmin(admin.ModelAdmin):
    model = models.Discount


class PriceQtyOverrideInline(admin.TabularInline):
    model = models.PriceQtyOverride
    extra = 0
    min_num = 0


class ProductVariantInline(admin.TabularInline):
    model = models.Variant
    extra = 0
    min_num = 1


class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    model = models.Product
    inlines = [ProductVariantInline, PriceQtyOverrideInline,]


class TaxAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'rate', 'rate_name',)


admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.Product, ProductAdmin)
admin.site.register(models.Maker)
admin.site.register(models.Discount, DiscountAdmin)
admin.site.register(models.Variant)
admin.site.register(models.Tax, TaxAdmin)
