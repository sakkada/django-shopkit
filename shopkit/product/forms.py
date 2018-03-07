from django import forms
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
