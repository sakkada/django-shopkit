# -*- coding:utf-8 -*-
from shopkit.cart.forms import (AddToCartForm as BaseAddToCartForm,
                                ReplaceCartLineForm)
from shop.core.app import shop_app


class AddToCartForm(shop_app.product_app.ProductVariantForm,
                    BaseAddToCartForm):
    pass
