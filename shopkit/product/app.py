from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.conf.urls import url
from ..core.app import ShopKitApp


class ProductApp(ShopKitApp):

    app_name = 'product'
    namespace = 'product'

    Product = None
    Variant = None

    product_details_templates = [
        'shopkit/product/view.html',
    ]

    def __init__(self, **kwargs):
        super(ProductApp, self).__init__(**kwargs)
        assert self.Product and self.Variant, (
            'You need to subclass ProductApp and provide Product and Variant.'
        )

    def get_product(self, request, product_pk=None):
        return get_object_or_404(self.Product, pk=product_pk)

    def on_product_view(self, product, request):
        """
        This method should be extended manually to provide additional
        functionality, like cart line adding processing.
        """
        return None

    # Views methods section
    # ---------------------
    def get_urls(self):
        return [
            url(r'^\+(?P<product_pk>[0-9]+)/$', self.product_details,
                name='details'),
        ]

    def product_details(self, request, **kwargs):
        product = self.get_product(request, **kwargs)
        context = self.on_product_view(product, request)
        if isinstance(context, HttpResponse):
            return context

        context = self.get_context_data(request, product=product, **context)
        return render(request, self.product_details_templates, context)
