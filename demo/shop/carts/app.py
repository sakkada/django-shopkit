from shopkit.cart import app, forms, handler, Cart


class CartApp(app.CartApp):
    Cart = Cart
    CartLineForm = forms.ReplaceCartLineForm
    AddToCartHandler = handler.AddToCartHandler
    AddToCartForm = forms.AddToCartForm

    def __init__(self, shop_app=None, **kwargs):
        if self.AddToCartHandler:
            shop_app.product_app.register_product_view_handler(
                self.AddToCartHandler(
                    cart_app=self, addtocart_formclass=self.AddToCartForm,
                    form_attribute='cart_form'
                )
            )
        super(CartApp, self).__init__(shop_app=shop_app, **kwargs)

    def get_cart_for_request(self, request):
        return self.Cart(request=request, shop_app=self.shop_app)
