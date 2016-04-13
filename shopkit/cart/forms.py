# -*- coding:utf-8 -*-
from django import forms
from django.core.exceptions import ObjectDoesNotExist, NON_FIELD_ERRORS
from django.utils.translation import ugettext_lazy as _
from satchless.item import InsufficientStock


class AddToCartForm(forms.Form):
    """
    Form that adds a Variant quantity to a Cart.
    It may be replaced by more advanced one, performing some checks.

    This form will be mixed with shopkit.product.forms.BaseVariantForm
    descendant form class (as last ancestor - Form(VariantForm, AddToCartForm))
    and will be used in on_product_view handler via
    cart.handler.AddToCartHandler (see product and cart app).
    """
    quantity = forms.DecimalField(initial=1)

    error_messages = {
        'empty-stock': _('Sorry. This product is currently out of stock.'),
        'variant-does-not-exists': _('Oops. We could not find that product.'),
        'insufficient-stock': _('Only %(remaining)s remaining in stock.'),
    }

    cart = None
    product = None

    def __init__(self, *args, **kwargs):
        self.cart = kwargs.pop('cart')
        self.product = kwargs.pop('product') # it is product instance
        super(AddToCartForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(AddToCartForm, self).clean()
        quantity = cleaned_data.get('quantity', None)
        if quantity is None:
            return cleaned_data

        try:
            variant = self.get_variant(cleaned_data)
        except ObjectDoesNotExist:
            msg = self.error_messages['variant-does-not-exists']
            self.add_error(NON_FIELD_ERRORS, msg)
        else:
            cart_line = self.cart.get_line(variant)
            old_quantity = cart_line.quantity if cart_line else 0
            new_quantity = quantity + old_quantity
            try:
                self.cart.check_quantity(variant, new_quantity, None)
            except InsufficientStock as e:
                remaining = e.item.get_stock() - old_quantity
                msg = self.error_messages[
                    'insufficient-stock' if remaining else 'empty-stock'
                ]
                self.add_error('quantity', msg % {'remaining': remaining,})
        return cleaned_data

    def save(self):
        """Adds CartLine into the Cart instance."""
        variant = self.get_variant(self.cleaned_data)
        self.cart.add(variant, self.cleaned_data['quantity'])
        return self.cart.get_line(variant)

    def add_error(self, name, value):
        errors = self.errors.setdefault(name, self.error_class())
        errors.append(value)

    def get_variant(self, cleaned_data):
        raise NotImplementedError()


class ReplaceCartLineForm(AddToCartForm):
    """
    Replaces quantity in CartLine.
    It may be replaced by more advanced one, performing some checks.

    This form will be used in cart_app as CartItemForm to update each
    cart_line object directly in cart main view.

    Note: product (self.product), received in __init__ is already
    variant object, because cart_line objects stores variant instances,
    not products in "product" attribute (it called so in satchless CartLine).

    Also it defines cart_line, because variant already defined.
    """
    signature = forms.IntegerField(initial=1, widget=forms.HiddenInput)
    cart_line = None

    def __init__(self, *args, **kwargs):
        super(ReplaceCartLineForm, self).__init__(*args, **kwargs)
        self.cart_line = self.cart.get_line(self.product) # it is variant

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        try:
            self.cart.check_quantity(self.product, quantity, None)
        except InsufficientStock as e:
            remaining = e.item.get_stock()
            msg = self.error_messages[
                'insufficient-stock' if remaining else 'empty-stock'
            ]
            raise forms.ValidationError(msg % {'remaining': remaining,})
        return quantity

    def clean(self):
        return super(AddToCartForm, self).clean() # do not call parent's clean

    def get_variant(self, cleaned_data):
        """In cart form product is already variant (see above cls docstring)"""
        return self.product

    def save(self):
        """Update cart_line (usually replace quantity)."""
        self.cart.add(self.product, self.cleaned_data['quantity'],
                      replace=True)
        return self.cart_line
