# -*- coding:utf-8 -*-
from django import forms
from shopkit.product.forms import BaseVariantForm
from . import models


class VariantWithSizeAndColorForm(BaseVariantForm):
    color = forms.CharField(
        max_length=10,
        widget=forms.Select(choices=models.Variant.COLOR_CHOICES))
    size = forms.CharField(
        max_length=10,
        widget=forms.Select(choices=models.Variant.SIZE_CHOICES))

    def __init__(self, *args, **kwargs):
        super(VariantWithSizeAndColorForm, self).__init__(*args, **kwargs)
        existing_choices = self.get_existing_variants_choices(
            self.get_base_variant_queryset(), ('color', 'size'))
        for field_name, choices in existing_choices.items():
            self.fields[field_name].widget.choices = choices

    def get_base_variant_queryset(self):
        """
        Return queryset of all available variants.
        May be extended if required to filter default queryset.
        """
        return self.product.variants.all()

    def get_variant_queryset(self):
        color = self.cleaned_data.get('color')
        size = self.cleaned_data.get('size')
        return self.get_base_variant_queryset().filter(color=color, size=size)

    def clean(self):
        if not self.get_variant_queryset().exists():
            raise forms.ValidationError("Variant does not exist")
        return super(VariantWithSizeAndColorForm, self).clean()

    def get_variant(self, cleaned_data):
        return self.get_variant_queryset().get()

    def get_existing_variants_choices(self, queryset, field_names):
        choices = {}
        variants = queryset.values_list(*field_names)

        if variants:
            for index, existing_choices in enumerate(zip(*variants)):
                field_name = field_names[index]
                all_values = queryset.model._meta.get_field(field_name).choices
                choices[field_name] = [c for c in all_values
                                       if c[0] in existing_choices]
        else:
            for field_name in field_names:
                choices[field_name] = []
        return choices
