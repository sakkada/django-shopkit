"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
"""
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap

#from shop.carts.app import cart_app
#from shop.categories.app import product_app
#from shop.orders.app import order_app
#from shop.checkouts.app import checkout_app
import shop.core.views
from shop.core.app import shop_app


urlpatterns = patterns('',
    url(r'^$', shop.core.views.home_page, name='home-page'),
    url(r'^admin/', include(include(admin.site.urls))),
    url(r'^thankyou/(?P<order_token>\w+)/$',
        shop.core.views.thank_you_page, name='thank-you'),
    url(r'^payment/failed/(?P<order_token>\w+)/$',
        shop.core.views.payment_failed, name='payment-failed'),

    url(r'^products/', include(shop_app.product_app.urls)),
    url(r'^cart/', include(shop_app.cart_app.urls)),
    url(r'^order/', include(shop_app.order_app.urls)),
    url(r'^checkout/', include(shop_app.checkout_app.urls)),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
