# -*- coding: utf-8 -*-
from django import dispatch

cart_line_changed = dispatch.Signal(providing_args=['cart', 'cart_line',])
cart_line_changed.__doc__ = """
Sent whenever cart's line has been changed, added or removed.
Technically, removed line is added with zero quantity, such cart_line will be
already removed from storage and will have zero quantity.
"""
