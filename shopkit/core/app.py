# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.urls import reverse
from django.shortcuts import redirect


class ShopKitApp(object):
    app_name = None
    namespace = None
    shop_app = None

    def __init__(self, name=None, shop_app=None):
        self.app_name = name or self.app_name
        self.shop_app = shop_app

    def get_context_data(self, request, **kwargs):
        context = {
            'current_app': self.app_name,
        }
        context.update(kwargs)
        return context

    def redirect(self, to, *args, **kwargs):
        uri = self.reverse(to, args=args, kwargs=kwargs)
        return redirect(uri)

    def reverse(self, to, args=None, kwargs=None):
        to = '%s:%s' % (self.namespace, to)
        return reverse(to, args=args, kwargs=kwargs, current_app=self.app_name)

    def get_urls(self):
        """
        Method returns same data, that regular urls.py contains.
        Each App class contains app_name and namespace, which are means
        application namespace and instance namespace in terms of django url
        resolving.
        To have explicit url configuration, it is good to directrly define
        get_urls method in App classes, combined with to or more ancestor
        classes, instead of usage method inheritance.
        Code in all builtin App classes structured such way: all views methods
        and method get_urls located in the end of class definition.
        """
        raise NotImplementedError('%s: get_urls is not implemented.' %
                                  type(self))

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.namespace


class ShopApp(ShopKitApp):
    product_app = None
    cart_app = None
    checkout_app = None
    order_app = None
