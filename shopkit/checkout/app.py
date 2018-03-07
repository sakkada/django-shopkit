from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf.urls import url

from ..core.app import ShopKitApp
from ..order import handler
from ..order.signals import order_pre_confirm
from ..payment import PaymentFailure, ConfirmationFormNeeded, RedirectRequired
from ..contrib.order.partitioner.simple import SimplePartitioner


class CheckoutApp(ShopKitApp):

    app_name = 'checkout'
    namespace = 'checkout'
    order_session_key = 'shop-order'

    Order = None

    confirmation_templates = [
        'shopkit/checkout/confirmation.html',
    ]

    def __init__(self, **kwargs):
        self.delivery_queue = kwargs.pop(
            'delivery_provider', handler.DeliveryQueue(
                *getattr(settings, 'SATCHLESS_DELIVERY_PROVIDERS', [])))
        self.payment_queue = kwargs.pop(
            'payment_provider', handler.PaymentQueue(
                *getattr(settings, 'SATCHLESS_PAYMENT_PROVIDERS', [])))
        self.delivery_partitioner = kwargs.pop(
            'delivery_partitioner', handler.PartitionerQueue(
                *getattr(settings, 'SATCHLESS_ORDER_PARTITIONERS', [
                    SimplePartitioner])))

        super(CheckoutApp, self).__init__(**kwargs)
        assert self.Order, (
            'You need to subclass CheckoutApp and provide Order model class.')

    def get_order(self, request, token):
        user = request.user if request.user.is_authenticated else None
        return self.Order.objects.filter(token=token, user=user).first()

    def get_order_from_cart(self, request, cart, order=None):
        if not order:
            order = self.Order.objects.create(cart=cart, user=cart.user)
        elif order.is_empty():
            order.groups.all().delete()

        self.partition_cart(cart, order)
        return order

    def partition_cart(self, cart, order, **pricing_context):
        partitions, remaining = self.delivery_partitioner.partition(cart, None)

        if remaining:
            raise ImproperlyConfigured('Unhandled items remaining in cart.')
        for partition in filter(None, partitions):
            delivery_group = order.create_delivery_group(partition)
            for cartline in partition:
                price = cartline.get_price_per_item(cart=cart,
                                                    **pricing_context)
                delivery_group.create_order_line(cartline.variant,
                                                 cartline.quantity, price)

    def clear_inactive_orders(self, order, cart, user=None):
        self.Order.objects.filter(
            Q(status=self.Order.SC.CHECKOUT, cart=cart) & ~Q(pk=order.pk)
        ).delete()

    def check_order(self, order, check_quantity=True):
        # check order and validate it for empty and empty groups
        checked = (order and not order.is_empty() and
                   not order.groups.filter(lines__isnull=True).exists())
        # check quantities if check_quantity is set
        if checked and check_quantity:
            checked = order.check_lines_quantities()

        return checked

    def redirect_order(self, order):
        if not order or order.is_empty():
            return self.shop_app.cart_app.redirect('details')
        elif order.status == order.SC.CHECKOUT and not self.check_order(order):
            return self.redirect('fix-order-lines', order_token=order.token)
        elif order.status == order.SC.CHECKOUT:
            return self.redirect('checkout', order_token=order.token)
        elif order.status == order.SC.PAYMENT_PENDING:
            return self.redirect('confirmation', order_token=order.token)
        return redirect('order:details', order_token=order.token)

    # Views methods section
    # ---------------------
    def get_urls(self):
        return [
            url(r'^prepare-order/$',
                self.prepare_order, name='prepare-order'),
            url(r'^(?P<order_token>[\w-]+)/fixorder/$',
                self.fix_order_lines, name='fix-order-lines'),
            url(r'^(?P<order_token>[\w-]+)/reactivate/$',
                self.reactivate_order, name='reactivate-order'),
            url(r'^(?P<order_token>[\w-]+)/confirmation/$',
                self.confirmation, name='confirmation'),
        ]

    def fix_order_lines(self, request, order_token=None, **kwargs):
        order = self.get_order(request, order_token)
        if not self.check_order(order):
            order.fix_lines_quantities()
            messages.warning(
                request, _('Your order was changed because of stock levels'
                           ' changed. Please try to checkout again.'))

        return self.redirect('checkout', order_token=order.token)

    @method_decorator(require_POST)
    def reactivate_order(self, request, order_token, **kwargs):
        order = self.get_order(request, order_token)
        if (not self.check_order(order) or
                order.status != order.CS.PAYMENT_FAILED):
            return self.redirect_order(order)

        order.set_status(order.SC.CHECKOUT)
        return self.redirect('checkout', order_token=order.token)

    @method_decorator(require_POST)
    def prepare_order(self, request, **kwargs):
        """
        Step 0: Prepare order.
        Create order object from cart or get created before by session key,
        check_quantity for cart and redirect to step 1.
        (next step is "checkout", no previous step, fully automated)
        """
        cart = self.shop_app.cart_app.get_cart_for_request(request)
        if cart.is_empty():
            return self.shop_app.cart_app.redirect('details')

        # check cart correctness and quantities (use cart_app internal check)
        if not self.shop_app.cart_app.check_cart(cart):
            return self.shop_app.cart_app.redirect('fix-cart-lines')

        # get order from session or create from cart and after check it
        order = request.session.get(self.order_session_key, None)
        if order:
            order = self.Order.objects.filter(
                token=order, status=self.Order.SC.CHECKOUT, cart=cart).first()
        if not order or order.is_empty():
            order = self.get_order_from_cart(request, cart, order=order)
        if not self.check_order(order):
            return self.redirect_order(order)

        # set user to order if required
        user = request.user if request.user.is_authenticated else None
        if user and order.user != user:
            order.user = user
            order.save()

        # clear waste (inactive) orders
        self.clear_inactive_orders(order, cart, user=user)

        request.session[self.order_session_key] = order.token
        return self.redirect('checkout', order_token=order.token)

    def confirmation(self, request, order_token, **kwargs):
        """
        Final step: Checkout confirmation.
        The final summary, where user is asked to review and confirm the order.
        Confirmation will redirect to the payment gateway.
        (no next step, previous step depends on CheckoutApp)
        """
        order = self.get_order(request, order_token)
        if (not self.check_order(order, check_quantity=False) or
                order.status != order.SC.PAYMENT_PENDING):
            return self.redirect_order(order)

        order_pre_confirm.send(sender=type(order), order=order,
                               request=request)

        try:
            self.payment_queue.confirm(order=order)
        except ConfirmationFormNeeded, e:
            return render(request, self.confirmation_templates,
                          {'formdata': e, 'order': order,})
        except RedirectRequired, e:
            return redirect(e.url)
        except PaymentFailure:
            order.set_status(order.SC.PAYMENT_FAILED)
        else:
            order.set_status(order.SC.PAYMENT_COMPLETE)

        return self.shop_app.order_app.redirect('details',
                                                order_token=order.token)
