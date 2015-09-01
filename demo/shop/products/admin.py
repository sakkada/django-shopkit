# -*- coding:utf-8 -*-
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms.models import modelform_factory
from django.utils.translation import ugettext_lazy as _, ugettext
import django.db.models

from shop.categories.admin.fields import CategoryMultipleChoiceField
from shop.core.app import shop_app
from . import models



class DiscountAdmin(admin.ModelAdmin):
    model = models.Discount


class ProductForm(forms.ModelForm):
    categories = CategoryMultipleChoiceField(
        required=False,
        queryset=shop_app.product_app.Category.objects.order_by('tree_id', 'lft'))

    class Meta:
        fields = '__all__'

product_fieldsets = (
    (_('General'), {
        'fields': ('name', 'description',)
    }),
    (_('Pricing'), {
        'fields': ('price', 'qty_mode', 'tax_group', 'discount'),
    }),
    (_('Categories'), {
        'fields': ('categories',),
    }),
)


class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    #prepopulated_fields = {'slug': ('name',)}


class PriceQtyOverrideInline(admin.TabularInline):
    model = models.PriceQtyOverride


class CardiganVariantInline(admin.TabularInline):
    model = models.CardiganVariant


class CardiganAdmin(ProductAdmin):
    model = models.Cardigan
    form = modelform_factory(models.Cardigan, form=ProductForm)
    inlines = [CardiganVariantInline, PriceQtyOverrideInline,]
    fieldsets = product_fieldsets


class DressVariantInline(admin.TabularInline):
    model = models.DressVariant


class DressAdmin(ProductAdmin):
    inlines = [DressVariantInline, PriceQtyOverrideInline,]
    form = modelform_factory(models.Dress, form=ProductForm)
    fieldsets = product_fieldsets


class HatForm(ProductForm, forms.ModelForm):
    stock_level = forms.DecimalField(max_digits=10, min_value=0)
    sku = forms.CharField()

    class Meta(ProductForm.Meta):
        model = models.Hat

    def __init__(self, *args, **kwargs):
        super(HatForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            variant = self.instance.variants.get()
            self.fields['stock_level'].initial = variant.stock_level
            self.fields['sku'].initial = variant.sku

    def clean_sku(self):
        sku = self.cleaned_data.get('sku', None)
        if sku is not None:
            query = Q(sku=sku)
            if self.instance.id:
                query &= ~Q(id=self.instance.variants.get().id)
            if models.Variant.objects.filter(query).exists():
                raise ValidationError(ugettext('Sku is not unique'))
        return sku


singlevariant_product_fieldsets = (
    (_('General'), {
        'fields': ('name', 'description',)
    }),
    (_('Pricing'), {
        'fields': ('price', 'tax_group', 'discount'),
    }),
    (_('Stock'), {
        'fields': ('sku', 'stock_level',),
    }),
    (_('Categories'), {
        'fields': ('categories',),
    }),
)


class HatAdmin(ProductAdmin):
    inlines = [PriceQtyOverrideInline,]
    fieldsets = singlevariant_product_fieldsets
    form = HatForm

    def save_model(self, request, obj, form, change):
        obj.save()
        if obj.variants.exists():
            variant = obj.variants.get()
        else:
            variant = models.HatVariant(product=obj)
        variant.stock_level = form.cleaned_data['stock_level']
        variant.sku = form.cleaned_data['sku']
        variant.save()


class JacketVariantInline(admin.TabularInline):
    model = models.JacketVariant


class JacketAdmin(ProductAdmin):
    inlines = [PriceQtyOverrideInline, JacketVariantInline,]
    fieldsets = product_fieldsets
    form = modelform_factory(models.Jacket, form=ProductForm)


class ShirtVariantInline(admin.TabularInline):
    model = models.ShirtVariant


class ShirtAdmin(ProductAdmin):
    inlines = [ShirtVariantInline, PriceQtyOverrideInline]
    fieldsets = product_fieldsets
    form = modelform_factory(models.Shirt, form=ProductForm)


class TrousersVariantInline(admin.TabularInline):
    model = models.TrousersVariant


class TrousersAdmin(ProductAdmin):
    inlines = [TrousersVariantInline, PriceQtyOverrideInline]
    fieldsets = product_fieldsets
    form = modelform_factory(models.Trousers, form=ProductForm)


class TShirtVariantInline(admin.TabularInline):
    model = models.TShirtVariant
    extra = 0
    min_num = 1


class TShirtAdmin(ProductAdmin):
    inlines = [TShirtVariantInline, PriceQtyOverrideInline]
    fieldsets = product_fieldsets
    form = modelform_factory(models.TShirt, form=ProductForm)


admin.site.register(models.Cardigan, CardiganAdmin)
admin.site.register(models.Dress, DressAdmin)
admin.site.register(models.Hat, HatAdmin)
admin.site.register(models.Jacket, JacketAdmin)
admin.site.register(models.Shirt, ShirtAdmin)
admin.site.register(models.Trousers, TrousersAdmin)
admin.site.register(models.TShirt, TShirtAdmin)

admin.site.register(models.Make)
admin.site.register(models.Discount, DiscountAdmin)

admin.site.register(models.Product)
admin.site.register(models.Variant)
