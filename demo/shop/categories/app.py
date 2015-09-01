from shopkit.contrib.product.category import app
from shop.products.models import Product, Variant
from .models import Category


class CategorizedProductApp(app.CategorizedProductApp):
    Category = Category
    Product = Product
    Variant = Variant
