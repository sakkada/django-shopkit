from django import forms
import inspect

from . import models

class BaseVariantForm(forms.Form):
    product = None

    def __init__(self, *args, **kwargs):
        variant = kwargs.pop('variant', None)
        super(BaseVariantForm, self).__init__(*args, **kwargs)
        assert isinstance(self.product, models.Product)

        # If we have a Variant, fill initials with data from the instance
        if variant:
            for field in variant._meta.fields:
                if not field.name in self.fields:
                    continue
                self.fields[field.name].initial = getattr(variant, field.name)


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

    def get_mixed_formclass(self, product_class, mixin_class=None,
                            mixin_first=False, class_name=None):
        """
        Return BaseVariantForm for product mixed with mixin_class.
        Allow set mixin_class as first ancestor and define final class name.
        Usually used for AddToCartForm, ect. class mixing.
        """
        
        variant_formclass = self.get_formclass(product_class)

        if mixin_first:
            bases = (mixin_class, variant_formclass,) 
        else:
            bases = (variant_formclass, mixin_class,) 

        class_name = class_name or 'MixedWith'.join(i.__name__ for i in bases)

        return type(class_name, bases, {})


registry = FormRegistry()



