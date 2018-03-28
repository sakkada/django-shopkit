from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render
from ....checkout import app


class SingleStepCheckoutApp(app.CheckoutApp):
    BillingForm = None

    checkout_templates = [
        'shopkit/checkout/checkout.html',
    ]

    def __init__(self, **kwargs):
        super(SingleStepCheckoutApp, self).__init__(**kwargs)
        assert self.BillingForm, ('You need to subclass SingleStepCheckoutApp'
                                  ' and provide BillingForm')

    # Views methods section
    # ---------------------
    def get_urls(self):
        return [
            url(r'^(?P<order_token>[\w-]+)/$', self.checkout, name='checkout'),
        ]

    def checkout(self, request, order_token, **kwargs):
        """
        Step 1 of 1: Checkout.
        The order is split into delivery groups and the user gets to pick
        both the delivery and payment methods.
        (next step is "confirmation", previous step is "prepare-order")
        """
        order = self.get_order(request, order_token)
        if not self.check_order(order) or order.status != order.SC.CHECKOUT:
            return self.redirect_order(order)

        delivery_groups = order.groups.all()
        for group in delivery_groups:
            delivery_types = list(self.delivery_queue.enum_types(group))
            if len(delivery_types) != 1:
                raise ImproperlyConfigured(
                    'The singlestep checkout requires exactly one delivery'
                    ' type per delivery group.')
            group.delivery_type = delivery_types[0].typ
            group.save()

        delivery_group_forms = self.delivery_queue.get_configuration_forms_for_groups(
            delivery_groups, request.POST or None)
        delivery_valid = True
        if request.method == 'POST':
            delivery_valid = True
            for group, delivery_type, form in delivery_group_forms:
                if form:
                    delivery_valid = delivery_valid and form.is_valid()

        payment_types = list(self.payment_queue.enum_types(order))
        if len(payment_types) != 1:
            raise ImproperlyConfigured(
                'The singlestep checkout requires exactly one payment methods.')
        order.payment_type = payment_types[0].typ
        order.save()

        billing_form = self.BillingForm(request.POST or None, instance=order)
        payment_form = self.payment_queue.get_configuration_form(order,
                                                                 request.POST)
        if request.method == 'POST':
            billing_valid = billing_form.is_valid()
            payment_valid = payment_form.is_valid() if payment_form else True
            if billing_valid and delivery_valid and payment_valid:
                order = billing_form.save()
                for group, typ, form in delivery_group_forms:
                    self.delivery_queue.save(group, form)
                self.payment_queue.save(order, payment_form)
                order.set_status(order.SC.PAYMENT_PENDING)
                return self.redirect('confirmation', order_token=order.token)

        context = self.get_context_data(
            request, billing_form=billing_form, payment_form=payment_form,
            delivery_group_forms=delivery_group_forms, order=order)
        return render(request, self.checkout_templates, context)
