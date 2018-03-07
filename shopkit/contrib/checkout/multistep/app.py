# -*- coding: utf-8 -*-
from django.forms.models import modelformset_factory
from django.shortcuts import render
from django.conf.urls import url
from ....checkout import app
from ....order import forms


class MultiStepCheckoutApp(app.CheckoutApp):
    BillingForm = None
    PaymentMethodForm = None
    DeliveryMethodForm = None
    DeliveryMethodFormSet = None
    ShippingForm = None
    ShippingFormSet = None
    VerificationForm = None

    checkout_templates = [
        'shopkit/checkout/checkout.html',
    ]
    delivery_method_templates = [
        'shopkit/checkout/delivery_method.html',
    ]
    delivery_details_templates = [
        'shopkit/checkout/delivery_details.html',
    ]
    payment_method_templates = [
        'shopkit/checkout/payment_method.html',
    ]
    payment_details_templates = [
        'shopkit/checkout/payment_details.html',
    ]
    verification_templates = [
        'shopkit/checkout/verification.html',
    ]

    def __init__(self, **kwargs):
        super(MultiStepCheckoutApp, self).__init__(**kwargs)
        assert (
            self.BillingForm and self.PaymentMethodForm and
            (self.ShippingForm or self.ShippingFormSet) and
            (self.DeliveryMethodForm or self.DeliveryMethodFormSet)
        ), (
            'You need to subclass MultiStepCheckoutApp and provide'
            ' BillingForm, PaymentMethodForm, and DeliveryMethod and Shipping'
            ' forms and/or formsets.'
        )

        self.ShippingFormSet = (
            self.ShippingFormSet or
            modelformset_factory(self.ShippingForm._meta.model,
                                 form=self.ShippingForm, extra=0))
        self.DeliveryMethodFormSet = (
            self.DeliveryMethodFormSet or
            modelformset_factory(self.DeliveryMethodForm._meta.model,
                                 formset=forms.DeliveryMethodFormSet,
                                 form=self.DeliveryMethodForm, extra=0))
        self.VerificationForm = self.VerificationForm or forms.VerificationForm

    # Views methods section
    # ---------------------
    def get_urls(self):
        return [
            url(r'^(?P<order_token>[\w-]+)/$',
                self.checkout, name='checkout'),
            url(r'^(?P<order_token>[\w-]+)/delivery-method/$',
                self.delivery_method, name='delivery-method'),
            url(r'^(?P<order_token>[\w-]+)/delivery-details/$',
                self.delivery_details, name='delivery-details'),
            url(r'^(?P<order_token>[\w-]+)/payment-method/$',
                self.payment_method, name='payment-method'),
            url(r'^(?P<order_token>[\w-]+)/payment-details/$',
                self.payment_details, name='payment-details'),
            url(r'^(?P<order_token>[\w-]+)/verification/$',
                self.verification, name='verification'),
        ]

    def checkout(self, request, order_token, **kwargs):
        """
        Step 1: Checkout step.
        If there are any shipping details needed, user will be asked for them.
        Otherwise redirect to step 2.
        (next step is "delivery-method", previous step is "prepare-order")
        """
        order = self.get_order(request, order_token)
        if not self.check_order(order) or order.status != order.SC.CHECKOUT:
            return self.redirect_order(order)

        billing_form = self.BillingForm(
            data=request.POST or None, instance=order)
        shipping_formset = self.ShippingFormSet(
            data=request.POST or None,
            queryset=order.groups.filter(shipping_address_required=True))

        if billing_form.is_valid() and shipping_formset.is_valid():
            order = billing_form.save()
            shipping_formset.save()
            return self.redirect('delivery-method', order_token=order.token)

        context = self.get_context_data(
            request, order=order, billing_form=billing_form,
            shipping_formset=shipping_formset)
        return render(request, self.checkout_templates, context)

    def delivery_method(self, request, order_token, **kwargs):
        """
        Step 2: Checkout step.
        User chooses delivery method for each of the delivery groups.
        (next step is "delivery-details", previous step is "checkout")
        """
        order = self.get_order(request, order_token)
        if not self.check_order(order) or order.status != order.SC.CHECKOUT:
            return self.redirect_order(order)

        delivery_method_formset = self.DeliveryMethodFormSet(
            data=request.POST or None, queryset=order.groups.all(),
            delivery_queue=self.delivery_queue)

        if delivery_method_formset.is_valid():
            delivery_method_formset.save()
            return self.redirect('delivery-details', order_token=order.token)

        context = self.get_context_data(
            request, order=order,
            delivery_method_formset=delivery_method_formset)
        return render(request, self.delivery_method_templates, context)

    def delivery_details(self, request, order_token, **kwargs):
        """
        Step 2½: Delivery details.
        User supplies further delivery details if needed.
        (next step is "payment-method", previous step is "delivery-method")
        """
        order = self.get_order(request, order_token)
        if not self.check_order(order) or order.status != order.SC.CHECKOUT:
            return self.redirect_order(order)
        delivery_groups = order.groups.all()
        if not all([group.delivery_type for group in delivery_groups]):
            return self.redirect('delivery-method', order_token=order.token)

        delivery_group_forms = self.delivery_queue.get_configuration_forms_for_groups(
            delivery_groups, request.POST or None)
        if all(form.is_valid() if form else True
               for group, delivery_type, form in delivery_group_forms):
            for group, delivery_type, form in delivery_group_forms:
                self.delivery_queue.save(group, form)
            return self.redirect('payment-method', order_token=order.token)

        context = self.get_context_data(
            request, order=order, delivery_group_forms=delivery_group_forms)
        return render(request, self.delivery_details_templates, context)

    def payment_method(self, request, order_token, **kwargs):
        """
        Step 3: Payment Method.
        User chooses the payment method.
        (next step is "payment-details", previous step is "delivery-details")
        """
        order = self.get_order(request, order_token)
        if not self.check_order(order) or order.status != order.SC.CHECKOUT:
            return self.redirect_order(order)

        payment_form = self.PaymentMethodForm(
            data=request.POST or None, instance=order,
            payment_queue=self.payment_queue)

        if payment_form.is_valid():
            payment_form.save()
            return self.redirect('payment-details', order_token=order.token)

        context = self.get_context_data(
            request, order=order, payment_form=payment_form)
        return render(request, self.payment_method_templates, context)

    def payment_details(self, request, order_token, **kwargs):
        """
        Step 3½: Payment details.
        If any payment details are needed, user will be asked for them.
        Otherwise we redirect to final confirmation step.
        (next step is "verification", previous step is "payment-method")
        """
        order = self.get_order(request, order_token)
        if not self.check_order(order) or order.status != order.SC.CHECKOUT:
            return self.redirect_order(order)
        if not order.payment_type:
            return self.redirect('payment-method', order_token=order.token)

        form = self.payment_queue.get_configuration_form(order,
                                                         request.POST or None)
        if not form or form.is_valid():
            self.payment_queue.save(order, form=form)
            return self.redirect('verification', order_token=order.token)

        context = self.get_context_data(request, form=form, order=order)
        return render(request, self.payment_details_templates, context)

    def verification(self, request, order_token, **kwargs):
        """
        Step 4: Verification
        Delivery and payment method and details already selected, and now
        we are ready to change order status and redirect to confirmation page.
        (next step is "confirmation", previous step is "payment-details")
        """
        order = self.get_order(request, order_token)
        if not self.check_order(order) or order.status != order.SC.CHECKOUT:
            return self.redirect_order(order)

        # delivery and payment data check
        if not all([group.delivery_type for group in order.groups.all()]):
            return self.redirect('delivery-method', order_token=order.token)
        if not order.payment_type:
            return self.redirect('payment-method', order_token=order.token)

        form = self.VerificationForm(
            data=request.POST or None, order=order,
            initial={'order_token': order.token,})

        if form.is_valid():
            order.set_status(order.SC.PAYMENT_PENDING)
            if order.status != order.SC.PAYMENT_PENDING:
                # stock_handler can revert status back to SC.CHECKOUT
                return self.redirect_order(order)
            return self.redirect('confirmation', order_token=order.token)

        context = self.get_context_data(request, order=order, form=form)
        return render(request, self.verification_templates, context)
