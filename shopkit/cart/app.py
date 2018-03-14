# -*- coding: utf-8 -*-
from django.http import HttpResponse, JsonResponse
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

    def get_form_for_cartline(self, request, cart, cart_line):
        prefix = 'cartline-%i' % cart_line.variant.id
        initial = {'quantity': cart_line.get_quantity(),}
        received = '%s-quantity' % prefix in request.POST
        form = self.CartLineReplaceForm(
            data=request.POST if received else None, prefix=prefix,
            cart=cart, variant=cart_line.variant, initial=initial)
        return form

    def on_cartline_form_valid(self, request, form, cart_line):
        form.save()

    def on_cart_view(self, cart, request):
        if not self.check_cart(cart):
            if request.is_ajax():
                return JsonResponse({'error': 'fix-cart-lines'}, status=400)
            return self.redirect('fix-cart-lines')

        cart_line_forms, valid = [], False
        for cart_line in cart:
            form = self.get_form_for_cartline(request, cart, cart_line)
            if form.is_valid():
                self.on_cartline_form_valid(request, form, cart_line)
                valid = True
            cart_line_forms.append(form)

        if request.is_ajax():
            return JsonResponse({
                'count': len(cart),
                'price': cart.get_total().gross,
                'currency': cart.get_currency(),
                'lines': {
                    form.cart_line.variant_id: {
                        'variant_id': form.cart_line.variant_id,
                        'quantity': form.cart_line.get_quantity(),
                        'unit_price': form.cart_line.get_price_per_item().gross,
                        'price': form.cart_line.get_total().gross,
                        'processed': form.is_bound,
                        'errors': form.errors or None,
                    } for form in cart_line_forms
                }
            })

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
