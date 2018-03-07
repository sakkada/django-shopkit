from django.http import Http404
from django.conf.urls import url
from django.shortcuts import render
from ....product import app


class CategorizedProductApp(app.ProductApp):

    app_name = 'category'
    Category = None
    category_details_templates = [
        'shopkit/category/view.html',
    ]
    category_list_templates = [
        'shopkit/category/list.html',
    ]

    def __init__(self, **kwargs):
        super(CategorizedProductApp, self).__init__(**kwargs)
        assert self.Category, ('You need to subclass CategorizedProductApp and'
                               ' provide Category.')

    def path_from_slugs(self, slugs):
        """
        Returns list of Category instances matching given slug path.
        """
        if len(slugs) == 0:
            return []
        leaves = self.Category.objects.filter(slug=slugs[-1])
        if not leaves:
            raise self.Category.DoesNotExist, "slug='%s'" % slugs[-1]
        for leaf in leaves:
            path = leaf.get_ancestors()
            if len(path) + 1 != len(slugs):
                continue
            if [c.slug for c in path] != slugs[:-1]:
                continue
            return list(path) + [leaf]
        raise self.Category.DoesNotExist

    def get_context_data(self, request, product=None, **kwargs):
        categories = self.Category.objects.filter(parent__isnull=True)
        context = dict(kwargs, categories=categories)
        if product:
            context.update({
                'path': product.category_path,
                'product': product,
            })
        return context

    def get_product(self, request, category_slugs='', product_pk=None):
        slugs = category_slugs.split('/')
        path = self.path_from_slugs(filter(None, slugs))
        products = self.Product.objects.all()
        if product_pk:
            products = products.filter(pk=product_pk)
        if len(path):
            products = products.filter(categories=path[-1])
        elif not request.user.is_staff:
            products = products.filter(categories__isnull=False)
        if not products.exists():
            raise Http404()
        product = products[0]
        product.category_path = path
        return product

    # Views methods section
    # ---------------------
    def get_urls(self):
        return [
            url(r'^$', self.category_list, name='category-index'),
            url(r'^(?P<category_slug>[\w-]+)/$',
                self.category_details, name='category-details',
                kwargs={'parent_slugs': '',}),
            url(r'^(?P<parent_slugs>([\w-]+/)*)(?P<category_slug>[\w-]+)/$',
                self.category_details, name='category-details'),
            url(r'^(?P<category_slugs>([\w-]+/)+)\+(?P<product_pk>\d+)/$',
                self.product_details, name='details'),
        ]

    def category_list(self, request, **kwargs):
        context = self.get_context_data(request)
        return render(request, self.category_list_templates, context)

    def category_details(self, request, parent_slugs, category_slug, **kwargs):
        slugs = filter(None, parent_slugs.split('/') + [category_slug])
        path = self.path_from_slugs(slugs)
        category = path[-1]

        context = self.get_context_data(request, category=category, path=path)
        return render(request, self.category_details_templates, context)
