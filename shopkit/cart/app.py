# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.conf.urls import url
from ..core.app import ShopKitApp


class CartApp(ShopKitApp):

    app_name = 'cart'
    namespace = 'cart'
    cart_session_key = 'shop-cart'

    Cart = None
    CartLineAddForm = None
    CartLineReplaceForm = None

    cart_view_templates = [
        'shopkit/cart/view.html'
    ]

    def __init__(self, **kwargs):
        super(CartApp, self).__init__(**kwargs)
        assert self.Cart, ('You need to subclass CartApp and provide Cart.')
        assert self.CartLineAddForm, (
            'You need to subclass CartApp and provide CartLineAddForm.')
        assert self.CartLineReplaceForm, (
            'You need to subclass CartApp and provide CartLineReplaceForm.')

    def get_cart_for_request(self, request):
        token = request.session.get(self.cart_session_key, None)
        user = request.user if request.user.is_authenticated else None

        if user:
            cart = user.carts.first() or self.Cart(user=user)
        elif token:
            cart = (self.Cart.objects.filter(token=token).first() or
                    self.Cart(token=token))
        else:
            cart = self.Cart()
            request.session[self.cart_session_key] = cart.token

        return cart

    def check_cart(self, cart, check_quantity=True):
        checked = True
        if check_quantity:
            checked = cart.check_lines_quantities()
        return checked

    def get_form_for_cartline(self, request, cart, line):
        prefix = 'cartline-%i' % line.variant.id
        initial = {'quantity': line.get_quantity(),}
        received = '%s-quantity' % prefix in request.POST
        form = self.CartLineReplaceForm(
            data=request.POST if received else None,
            prefix=prefix, cart=cart, variant=line.variant, initial=initial)
        return form

    def on_cartline_form_valid(self, request, form, line):
        form.save()

    def on_cart_view(self, cart, request):
        if not self.check_cart(cart):
            return self.redirect('fix-cart-lines')

        cart_line_forms, valid = [], False
        for line in cart:
            form = self.get_form_for_cartline(request, cart, line)
            if form.is_valid():
                result = self.on_cartline_form_valid(request, form, line)
                if result:
                    return result
                valid = True
            cart_line_forms.append(form)

        # refresh current page if at least one valid form
        return redirect('./') if valid else {
            'cart': cart, 'cart_line_forms': cart_line_forms,
        }

    # Views methods section
    # ---------------------
    def get_urls(self):
        return [
            url(r'^fixcart/$', self.fix_cart_lines, name='fix-cart-lines'),
            url(r'^view/$', self.cart_view, name='details'),
        ]

    def fix_cart_lines(self, request, **kwargs):
        cart = self.get_cart_for_request(request)
        if not self.check_cart(cart):
            cart.fix_lines_quantities()
            messages.warning(
                request, _('Your cart was changed because of stock levels'
                           ' changed. Please check all your products again.'))

        return self.redirect('details')

    def cart_view(self, request, **kwargs):
        cart = self.get_cart_for_request(request)
        context = self.on_cart_view(cart, request)
        if isinstance(context, HttpResponse):
            return context

        context = self.get_context_data(request, **context)
        return render(request, self.cart_view_templates, context)
