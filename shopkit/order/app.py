from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.conf.urls import url
from ..core.app import ShopKitApp


class OrderApp(ShopKitApp):

    app_name = 'order'
    namespace = 'order'

    Order = None
    DeliveryGroup = None
    OrderLine = None

    order_list_templates = [
        'shopkit/order/list.html',
    ]
    order_details_templates = [
        'shopkit/order/view.html',
    ]

    def __init__(self, **kwargs):
        super(OrderApp, self).__init__(**kwargs)
        assert self.Order and self.DeliveryGroup and self.OrderLine, (
            'You need to subclass OrderApp and provide Order,'
            ' DeliveryGroup and OrderLine.'
        )

    def get_order(self, request, order_token):
        orders = self.Order.objects.filter(
            user=request.user if request.user.is_authenticated() else None)
        return get_object_or_404(orders, token=order_token)

    # Views methods section
    # ---------------------
    def get_urls(self):
        return [
            url(r'^$', self.index, name='index'),
            url(r'^(?P<order_token>[\w-]+)/$', self.details,
                name='details'),
        ]

    @method_decorator(login_required)
    def index(self, request, **kwargs):
        orders = self.Order.objects.filter(user=request.user)
        context = self.get_context_data(request, orders=orders)
        return render(request, self.order_list_templates, context)

    def details(self, request, order_token, **kwargs):
        order = self.get_order(request, order_token=order_token)
        context = self.get_context_data(request, order=order)
        return render(request, self.order_details_templates, context)
