# -*- coding: utf-8 -*-
from shopkit.core.app import ShopApp

# instantiate shop_app and all other
# note: importing and instantiating order are very important
# https://groups.google.com/d/msg/comp.lang.python/HYChxtsrhnw/AeCAK6zM9Q4J

shop_app = ShopApp()

from shop.categories.app import CategorizedProductApp
shop_app.product_app = CategorizedProductApp(shop_app=shop_app)

from shop.carts.app import CartApp
shop_app.cart_app = CartApp(shop_app=shop_app)

from shop.orders.app import OrderApp
shop_app.order_app = OrderApp(shop_app=shop_app)

from shop.checkouts.app import CheckoutApp
shop_app.checkout_app = CheckoutApp(shop_app=shop_app)
