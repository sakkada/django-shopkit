from django import forms
import inspect

from . import models

class BaseVariantForm(forms.Form):
    product = None

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product')
        variant = kwargs.pop('variant', None)
        super(BaseVariantForm, self).__init__(*args, **kwargs)
        # If we have a Variant, fill initials with data from the instance
        if variant:
            for field in variant._meta.fields:
                name = field.name
                if not self.fields.has_key(name):
                    continue
                self.fields[name].initial = getattr(variant, name)


class FormRegistry(object):
    variant_form_classes = None

    def __init__(self):
        self.variant_form_classes = {}

    def register(self, product_class, form_class=None):
        assert issubclass(product_class, models.Product)
        if form_class is None:
            # @registry.register(product_class)
            # class FormClass: pass
            def dec(form_cls):
                self.register(product_class, form_cls)
                return form_class
            return dec
        else:
            # registry.register(product_class, form_class)
            assert issubclass(form_class, BaseVariantForm)
            self.variant_form_classes[product_class] = form_class

    def get_formclass(self, product_class):
        classes = inspect.getmro(product_class)
        for c in classes:
            if c in self.variant_form_classes:
                return self.variant_form_classes[c]
        raise ValueError('No form class returned for %s. Make sure that your'
                         ' forms module is loaded.' % (product_class, ))


registry = FormRegistry()
