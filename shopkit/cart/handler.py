from django.shortcuts import redirect
from ..product.models import Product, Variant
from ..product.forms import registry
from . import forms, signals


class AddToCartHandler(object):
    """
    Parametrized handler for `product_view`, which produces *add to cart* forms,
    validates them and performs all the logic of adding an item to a cart.
    """

    def __init__(self, cart_app, addtocart_formclass=forms.AddToCartForm,
                 form_attribute='cart_form'):
        """
        Sets up a parametrized handler for product view.
        Accepts:
            cart_app: the cart application isinstance,
            addtocart_formclass: form class for adding to cart,
            form_attribute: name of product's attribute to save the form under.
        """
        self.cart_app = cart_app
        self.form_attribute = form_attribute
        self.addtocart_formclass = addtocart_formclass

    def __call__(self, instances=None, request=None, extra_context=None,
                 **kwargs):
        """
        Accepts a list of Product or Variant instances. For every of them create
        add-to-cart form. For a POST request, performs validation and if it
        succeeds, adds item to cart and returns redirect to the cart page.
        It handles adding only a single variant to the cart, but with the
        quantity specified in request.
        Accepts:
            instances: products and/or variants being viewed,
            request: the HTTP request instance,
            extra_context: extra context that will be passed to template.
        """
        for instance in instances:
            if isinstance(instance, Variant):
                product = instance.product
                variant = instance
            elif isinstance(instance, Product):
                product = instance
                variant = None
            else:
                raise ValueError("Received unknown type: %s" % type(instance))

            cart = self.cart_app.get_cart_for_request(request)
            Form = registry.get_mixed_formclass(
                type(product), mixin_class=self.addtocart_formclass,
                mixin_first=False, class_name='AddVariantToCartForm')

            if request.method == 'POST':
                form = Form(cart=cart, data=request.POST, product=product,
                            variant=variant)
                if form.is_valid():
                    cart_line = form.save()
                    signals.cart_item_added.send(sender=type(cart_line),
                                                 request=request,
                                                 cart=cart,
                                                 cart_line=cart_line)
                    return self.on_success(request, form, cart, cart_line)
            else:
                form = Form(cart=cart, data=None, product=product,
                            variant=variant)

            # Attach the form to instance to form_attribute
            setattr(instance, self.form_attribute, form)
        return extra_context

    def on_success(self, request, form, cart, cart_line):
        return redirect(self.cart_app.reverse('details'))
