from collections import defaultdict
from django.db import models
from django.db.models.fields.related import SingleRelatedObjectDescriptor
from django.dispatch import receiver
from django.core import checks


class SubtypedManager(models.Manager):

    def find_subclasses(self, root):
        for a in dir(root):
            attr = getattr(root, a)
            if isinstance(attr, SingleRelatedObjectDescriptor):
                child = attr.related.model
                if (issubclass(child, root) and
                    child is not root):
                    yield a
                    for s in self.find_subclasses(child):
                        yield '%s__%s' % (a, s)

    # https://code.djangoproject.com/ticket/16572
    #def get_query_set(self):
    #    qs = super(SubtypedManager, self).get_query_set()
    #    subclasses = list(self.find_subclasses(self.model))
    #    if subclasses:
    #        return qs.select_related(*subclasses)
    #    return qs


class Subtyped(models.Model):

    subtype_attr = models.CharField(max_length=500, editable=False)
    __in_unicode = False

    objects = SubtypedManager()

    class Meta:
        abstract = True

    def __unicode__(self):
        # XXX: can we do it in more clean way?
        if self.__in_unicode:
            return unicode(super(Subtyped, self))
        subtype_instance = self.get_subtype_instance()
        if type(subtype_instance) is type(self):
            self.__in_unicode = True
            res = self.__unicode__()
            self.__in_unicode = False
            return res
        return subtype_instance.__unicode__()

    def get_subtype_instance(self):
        """
        Caches and returns the final subtype instance. If refresh is set,
        the instance is taken from database, no matter if cached copy
        exists.
        """
        subtype = self
        path = self.subtype_attr.split()
        whoami = self._meta.model_name
        remaining = path[path.index(whoami) + 1:]
        for r in remaining:
            subtype = getattr(subtype, r)
        return subtype

    def store_subtype(self, klass):
        if not self.id:
            path = [self]
            parents = self._meta.parents.keys()
            while parents:
                parent = parents[0]
                path.append(parent)
                parents = parent._meta.parents.keys()
            path = [p._meta.model_name for p in reversed(path)]
            self.subtype_attr = ' '.join(path)


@receiver(models.signals.pre_save)
def _store_content_type(sender, instance, **kwargs):
    if isinstance(instance, Subtyped):
        instance.store_subtype(instance)



class Checker(object):
    def check(self, cls, errors, **kwargs):
        raise NotImplementedError


class FieldsChecker(object):
    fields = None
    
    def __init__(self, fields=None):
        self.fields = fields

    def check(self, cls, errors, **kwargs):
        modelfields = dict([(i.name, i,) for i in cls._meta.get_fields()])
        for cname, cfield in self.fields.items():
            field = modelfields.get(cname, None)
            if field:
                valid, ckey, cval = True, None, None
                for ckey, cval in cfield.items():
                    if ckey == 'type':
                        if not isinstance(field, cval):
                            valid = False
                            break
                    else:
                        ckeys, fvalue = ckey.split('.'), field
                        for i in ckeys:
                            i, call = ((i[:-2], True,)
                                       if i.endswith('()') else (i, False,))
                            fvalue = getattr(fvalue, i, None)
                            fvalue = fvalue() if call else fvalue

                        if not fvalue == cval:
                            valid = False
                            break
                if valid:
                    continue

                errors.append(checks.Error(
                    "Field '%s:%s' does not passed rule '%s:%s'."
                    % (cls.__name__, cname, ckey, cval,),
                    hint=None, obj=None, id='shopkit.E002'
                ))
            else:
                errors.append(checks.Error(
                    "Model '%s' does not contains field '%s'."
                    % (cls.__name__, cname,),
                    hint=None, obj=None, id='shopkit.E001'
                ))
                

class CheckModelMixin(object):
    checkers = None
    
    @classmethod
    def check(cls, **kwargs):
        errors = super(CheckModelMixin, cls).check(**kwargs)
        for check in cls.checkers or []:
            check.check(cls, errors, **kwargs)
        return errors


"""
class Product(models.Product):
    checkers = [
        FieldsChecker({'user': {'type': ForeignKey},})
    ]

class SomeProduct(Product):
    checkers = Product.checkers + [
        FieldsChecker({'user': {'type': ForeignKey},})
    ]
"""

