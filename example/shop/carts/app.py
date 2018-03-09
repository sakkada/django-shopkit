from django.conf.urls import url
from shopkit.cart import app
from . import forms
from . import models


class CartApp(app.CartApp):
    Cart = models.Cart
    CartLineAddForm = forms.CartLineAddForm
    CartLineReplaceForm = forms.CartLineReplaceForm

    def get_cart_for_request(self, request, previous_for_merge=False):
        token = request.session.get(self.cart_session_key, None)
        user = request.user if request.user.is_authenticated else None

        if previous_for_merge:
            return self.Cart.objects.filter(token=token).first()

        if user:
            cart = user.carts.first() or self.Cart(user=user)
        elif token:
            cart = (self.Cart.objects.filter(token=token).first() or
                    self.Cart(token=token))
        else:
            cart = self.Cart()
            request.session[self.cart_session_key] = cart.token

        return cart

    # Views methods section
    # ---------------------
    def get_urls(self):
        return [
            url(r'^fixcart/$', self.fix_cart_lines, name='fix-cart-lines'),
            url(r'^view/$', self.cart_view, name='details'),
        ]
