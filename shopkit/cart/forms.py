# -*- coding:utf-8 -*-
from django import forms
from django.core.exceptions import ObjectDoesNotExist, NON_FIELD_ERRORS
from django.utils.translation import ugettext_lazy as _
from satchless.item import InsufficientStock


class CartLineAddForm(forms.Form):
    """
    Form that adds a Variant with a quantity to a Cart.
    It may be replaced by more advanced one, performing some checks.

    This form will be mixed with shopkit.product.forms.BaseVariantForm
    form class (as last ancestor - Form(VariantForm, CartLineAddForm)).

    This form should be used in product_app.product_details or
    product_app.on_product_view custom method to add new product's
    variant to a cart. See example product's product_app.on_product_view
    method for more details.
    """
    quantity = forms.IntegerField(
        label=_('quantity'), initial=1, min_value=0, max_value=999)

    error_messages = {
        'not-available': _('Sorry. This product is currently not available.'),
        'empty-stock': _('Sorry. This product is currently out of stock.'),
        'variant-does-not-exists': _('Oops. We could not find that product.'),
        'insufficient-stock': _('Only %d remaining in stock.'),
        'reduced-stock': _('Product Stock have reduced after addition to cart'
                           ' on %d items, quantity should be reduced.'),
    }

    cart = None
    product = None

    def __init__(self, *args, **kwargs):
        self.cart = kwargs.pop('cart')
        self.product = kwargs.pop('product')  # it is a Product instance
        super(CartLineAddForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(CartLineAddForm, self).clean()
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
            cart_line_quantity = cart_line.quantity if cart_line else 0
            try:
                variant.check_quantity(quantity)
            except InsufficientStock as e:
                remaining = e.item.get_stock()
                qty_delta = remaining - cart_line_quantity
                if qty_delta < 0:
                    msg = self.error_messages['reduced-stock'] % abs(qty_delta)
                elif remaining:
                    msg = self.error_messages['insufficient-stock'] % remaining
                else:
                    msg = self.error_messages['empty-stock']
                self.add_error('quantity', msg)
        return cleaned_data

    def save(self):
        """Adds CartLine into the Cart instance."""
        variant = self.get_variant(self.cleaned_data)
        return self.cart.add(
            variant, quantity=self.cleaned_data['quantity'], replace=True)

    def get_variant(self, cleaned_data):
        raise NotImplementedError()


class CartLineReplaceForm(CartLineAddForm):
    """
    Replaces quantity in CartLine.
    It may be replaced by more advanced one, performing some checks.

    This form will be used in cart_app as CartLineReplaceForm to update each
    cart_line object directly in cart main view.
    """

    variant = None
    cart_line = None

    def __init__(self, *args, **kwargs):
        self.variant = kwargs.pop('variant')

        super(CartLineReplaceForm, self).__init__(
            *args, **dict(kwargs, product=self.variant.product))

        self.cart_line = self.cart.get_line(self.variant)
        # todo: check is cart_line exists in cart

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        try:
            self.variant.check_quantity(quantity)
        except InsufficientStock as e:
            remaining = e.item.get_stock()
            qty_delta = remaining - self.cart_line.quantity
            if qty_delta < 0:
                msg = self.error_messages['reduced-stock'] % abs(qty_delta)
            elif remaining:
                msg = self.error_messages['insufficient-stock'] % remaining
            else:
                msg = self.error_messages['empty-stock']
            raise forms.ValidationError(msg)
        return quantity

    def clean(self):
        # call CartLineAddForm parent's clean directly
        return super(CartLineAddForm, self).clean()

    def get_variant(self, cleaned_data):
        """In cart form variant is already exists."""
        return self.variant

    def save(self):
        """Update cart_line (replace quantity)."""
        return self.cart.add(
            self.variant, quantity=self.cleaned_data['quantity'], replace=True)
