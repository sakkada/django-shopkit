# -*- coding: utf-8 -*-
from django import dispatch

cart_content_changed = dispatch.Signal(providing_args=['cart', 'cart_line',])
cart_content_changed.__doc__ = """
Sent whenever cart's content has been changed.
"""

cart_item_added = dispatch.Signal(providing_args=['request', 'cart','cart_line',])
cart_item_added.__doc__ = """
Sent whenever new item is added to the cart.
"""
