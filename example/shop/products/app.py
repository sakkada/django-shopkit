from django.shortcuts import redirect, render
from django.conf.urls import url
from shopkit.contrib.product.category import app
from shop.products.models import Product, Variant
from .models import Category
from .forms import VariantWithSizeAndColorForm


class ProductApp(app.CategorizedProductApp):
    Category = Category
    Product = Product
    Variant = Variant
    ProductVariantForm = VariantWithSizeAndColorForm

    def on_product_view(self, product, request):
        # cart form processing
        cart = self.shop_app.cart_app.get_cart_for_request(request)
        form = self.shop_app.cart_app.CartLineAddForm(
            data=request.POST or None, cart=cart, product=product)
        if form.is_valid():
            cart_line = form.save()
            return redirect(self.shop_app.cart_app.reverse('details'))

        return {'cart_form': form,}

    # Views methods section
    # ---------------------
    def get_urls(self):
        return [
            url(r'^$', self.category_list, name='category-index'),
            url(r'^(?P<category_slug>[\w-]+)/$',
                self.category_details, name='category-details',
                kwargs={'parent_slugs': '',}),
            url(r'^(?P<parent_slugs>([\w-]+/)*)(?P<category_slug>[\w-]+)/$',
                self.category_details, name='category-details'),
            url(r'^(?P<category_slugs>([\w-]+/)+)\+(?P<product_pk>\d+)/$',
                self.product_details, name='details'),
        ]
