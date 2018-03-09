# -*- coding:utf-8 -*-
from shopkit.cart.forms import (CartLineAddForm as BaseCartLineAddForm,
                                CartLineReplaceForm)
from shop.core.app import shop_app


class CartLineAddForm(shop_app.product_app.ProductVariantForm,
                      BaseCartLineAddForm):
    pass
