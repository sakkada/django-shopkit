# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from . import forms
from . import handler
from . import models
from ..core.app import SatchlessApp, view
from ..utils import JSONResponse


class CartApp(SatchlessApp):

    app_name = 'cart'
    namespace = 'cart'
    CartLineForm = None
    Cart = None

    cart_templates = [
        'satchless/cart/view.html'
    ]

    def __init__(self, **kwargs):
        super(CartApp, self).__init__(**kwargs)
        assert self.Cart, ('You need to subclass CartApp and provide Cart')
        assert self.CartLineForm, ('You need to subclass CartApp and'
                                   ' provide CartLineForm')

    def get_cart_for_request(self, request):
        raise NotImplementedError()

    def _get_cart_item_form(self, request, cart, item):
        initial = {'quantity': item.get_quantity() or None,}
        form = self.CartLineForm(data=request.POST or None,
                                 cart=cart,
                                 product=item.product,
                                 prefix='cart-%i' % (item.product.id,),
                                 initial=initial)
        return form

    def cart_item_form_valid(self, request, form, item):
        form.save()
        return redirect(request.get_full_path())

    def _handle_cart(self, cart, request):
        cart_item_forms = []
        for item in cart:
            form = self._get_cart_item_form(request, cart, item)
            if request.method == 'POST' and form.is_valid():
                return self.cart_item_form_valid(request, form, item)
            cart_item_forms.append(form)
        return {
            'cart': cart,
            'cart_item_forms': cart_item_forms,
        }

    @view(r'^view/$', name='details')
    def cart(self, request):
        cart = self.get_cart_for_request(request)
        context = self._handle_cart(cart, request)
        if isinstance(context, HttpResponse):
            return context
        context = self.get_context_data(request, **context)
        response = TemplateResponse(request, self.cart_templates, context)
        if request.is_ajax():
            return JSONResponse({'total': len(cart),
                                 'html': response.rendered_content})
        return response

    @view(r'^remove/(?P<item_pk>[0-9]+)/$', name='remove-item')
    @method_decorator(require_POST)
    def remove_item(self, request, item_pk):
        cart = self.get_cart_for_request(request)
        try:
            item = cart.get_item(pk=item_pk)
        except ObjectDoesNotExist:
            return HttpResponseNotFound()
        cart.replace_item(item.variant, 0)
        return self.redirect('details')

    def get_cart_for_request(self, request):
        raise NotImplementedError
