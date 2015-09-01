from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from ..core.app import SatchlessApp, view
from ..order import handler
from ..order.signals import order_pre_confirm
from ..payment import PaymentFailure, ConfirmationFormNeeded
from ..contrib.order.partitioner.simple import SimplePartitioner


class CheckoutApp(SatchlessApp):

    app_name = 'checkout'
    namespace = 'checkout'
    order_session_key = 'checkout-order'

    Order = None
    confirmation_templates = [
        'satchless/checkout/confirmation.html',
    ]

    def __init__(self, **kwargs):
        self.delivery_queue = kwargs.pop('delivery_provider',
            handler.DeliveryQueue(*getattr(settings, 'SATCHLESS_DELIVERY_PROVIDERS', [])))

        self.payment_queue = kwargs.pop('payment_provider',
            handler.PaymentQueue(*getattr(settings, 'SATCHLESS_PAYMENT_PROVIDERS', [])))

        self.delivery_partitioner = kwargs.pop('delivery_partitioner',
            handler.PartitionerQueue(*getattr(settings, 'SATCHLESS_ORDER_PARTITIONERS',
                                              [SimplePartitioner])))

        super(CheckoutApp, self).__init__(**kwargs)
        assert self.Order, ('You need to subclass CheckoutApp and provide Order')

    def redirect_order(self, order):
        if not order or order.is_empty():
            return self.shop_app.cart_app.redirect('details')
        elif order.status == 'checkout':
            return self.redirect('checkout', order_token=order.token)
        elif order.status == 'payment-pending':
            return self.redirect('confirmation', order_token=order.token)
        return redirect('order:details', order_token=order.token)

    def get_order(self, request, order_token):
        try:
            return self.Order.objects.get(token=order_token)
        except self.Order.DoesNotExist:
            return

    def get_order_from_cart(self, request, cart, order=None):
        if not order:
            order = self.Order.objects.create()
        elif order.is_empty():
            order.groups.all().delete()

        self.partition_cart(cart, order)
        return order

    def clear_cart(self, request):
        cart = self.shop_app.cart_app.get_cart_for_request(request)
        cart.clear()
        return cart

    def partition_cart(self, cart, order, **pricing_context):
        partitions, remaining = self.delivery_partitioner.partition(cart, None)
        
        if remaining:
            raise ImproperlyConfigured('Unhandled items remaining in cart.')
        for partition in filter(None, partitions):
            delivery_group = order.create_delivery_group(partition)
            for cartline in partition:
                price = cartline.get_price_per_item(cart=cart,
                                                    **pricing_context)
                delivery_group.add_item(cartline.product,
                                        cartline.quantity, price)

    @view(r'^prepare-order/$', name='prepare-order')
    @method_decorator(require_POST)
    def prepare_order(self, request):
        cart = self.shop_app.cart_app.get_cart_for_request(request)
        if not len(cart):
            return self.shop_app.cart_app.redirect('details')

        order = request.session.get(self.order_session_key, None)
        if order:
            try:
                order = self.Order.objects.get(pk=order, status='checkout')
            except self.Order.DoesNotExist:
                order = None

        if not order or order.is_empty():
            order = self.get_order_from_cart(request, cart)

        # set user to order and erase all previous orders in checkout status
        user = request.user if request.user.is_authenticated() else None
        if user and order.user != user:
            order.user = user
            order.save()
        if user:
            self.Order.objects.filter(status='checkout',
                                      user=user).exclude(pk=order.pk).delete()

        request.session[self.order_session_key] = order.pk
        return self.redirect('checkout', order_token=order.token)

    @view(r'^(?P<order_token>\w+)/reactivate/$', name='reactivate-order')
    @method_decorator(require_POST)
    def reactivate_order(self, request, order_token):
        order = self.get_order(request, order_token)
        if not order or order.status != 'payment-failed':
            return self.redirect_order(order)
        order.set_status('checkout')
        return self.redirect('checkout', order_token=order.token)

    @view(r'^(?P<order_token>\w+)/confirmation/$', name='confirmation')
    def confirmation(self, request, order_token):
        """
        Checkout confirmation
        The final summary, where user is asked to review and confirm the order.
        Confirmation will redirect to the payment gateway.
        """
        order = self.get_order(request, order_token)
        if not order or order.status != 'payment-pending':
            return self.redirect_order(order)

        order_pre_confirm.send(sender=self.Order, instance=order,
                               request=request)
        try:
            self.payment_queue.confirm(order=order)
        except ConfirmationFormNeeded, e:
            return TemplateResponse(request, self.confirmation_templates,
                                    {'formdata': e, 'order': order,})
        except RedirectNeeded, e:
            return redirect(e.url)
        except PaymentFailure:
            order.set_status('payment-failed')
        else:
            order.set_status('payment-complete')
        return redirect('order:details', order_token=order.token)
