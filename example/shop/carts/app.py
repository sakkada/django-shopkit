from django.conf.urls import url
from shopkit.cart import app
from . import forms
from . import models


class CartApp(app.CartApp):
    Cart = models.Cart
    CartLineForm = forms.ReplaceCartLineForm
    AddToCartForm = forms.AddToCartForm

    # Views methods section
    # ---------------------
    def get_urls(self):
        return [
            url(r'^fixcart/$', self.fix_cart_lines, name='fix-cart-lines'),
            url(r'^view/$', self.cart_view, name='details'),
        ]
