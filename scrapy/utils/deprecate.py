"""Some helpers for deprecation messages"""

import warnings
import inspect
from scrapy.exceptions import ScrapyDeprecationWarning


def attribute(obj, oldattr, newattr, version='0.12'):
    cname = obj.__class__.__name__
    warnings.warn("%s.%s attribute is deprecated and will be no longer supported "
        "in Scrapy %s, use %s.%s attribute instead" % \
        (cname, oldattr, version, cname, newattr), ScrapyDeprecationWarning, stacklevel=3)


def create_deprecated_class(name, new_class, clsdict=None,
                            warn_category=ScrapyDeprecationWarning,
                            subclass_warn_message="{cls} inherits from "\
                                    "deprecated class {old}, please inherit "\
                                    "from {new}.",
                            instance_warn_message="{cls} is deprecated, "\
                                    "instantiate {new} instead."):
    """
    Return a "deprecated" class that causes its subclasses to issue a warning.
    Subclasses of ``new_class`` are considered subclasses of this class.
    It also warns when the deprecated class is instantiated, but do not when
    its subclasses are instantiated.

    It can be used to rename a base class in a library. For example, if we
    have

        class OldName(SomeClass):
            # ...

    and we want to rename it to NewName, we can do the following::

        class NewName(SomeClass):
            # ...

        OldName = create_deprecated_class('OldName', NewName)

    Then, if user class inherits from OldName, warning is issued. Also, if
    some code uses ``issubclass(sub, OldName)`` or ``isinstance(sub(), OldName)``
    checks they'll still return True if sub is a subclass of NewName instead of
    OldName.
    """

    class DeprecatedClass(type):

        deprecated_class = None

        def __new__(metacls, name, bases, clsdict_):
            cls = super(DeprecatedClass, metacls).__new__(metacls, name, bases, clsdict_)
            if metacls.deprecated_class is None:
                metacls.deprecated_class = cls
            return cls

        def __init__(cls, name, bases, clsdict_):
            old = cls.__class__.deprecated_class
            if cls is not old:
                msg = subclass_warn_message.format(cls=_clspath(cls),
                                                   old=_clspath(old),
                                                   new=_clspath(new_class))
                warnings.warn(msg, warn_category, stacklevel=2)
            super(DeprecatedClass, cls).__init__(name, bases, clsdict_)

        # see http://www.python.org/dev/peps/pep-3119/#overloading-isinstance-and-issubclass
        # and http://docs.python.org/2/reference/datamodel.html#customizing-instance-and-subclass-checks
        # for implementation details
        def __instancecheck__(cls, inst):
            return any(cls.__subclasscheck__(c)
                       for c in {type(inst), inst.__class__})

        def __subclasscheck__(cls, sub):
            if not inspect.isclass(sub):
                raise TypeError("issubclass() arg 1 must be a class")

            mro = getattr(sub, '__mro__', ())
            candidates = {cls, new_class}
            return any(c in candidates for c in mro)

        def __call__(cls, *args, **kwargs):
            if cls is cls.__class__.deprecated_class:
                msg = instance_warn_message.format(cls=_clspath(cls),
                                                   new=_clspath(new_class))
                warnings.warn(msg, warn_category, stacklevel=2)
            return super(DeprecatedClass, cls).__call__(*args, **kwargs)

    deprecated_cls = DeprecatedClass(name, (new_class,), clsdict or {})
    frm = inspect.stack()[1]
    parent_module = inspect.getmodule(frm[0])
    if parent_module is not None:
        deprecated_cls.__module__ = parent_module.__name__

    return deprecated_cls


def _clspath(cls):
    return '{}.{}'.format(cls.__module__, cls.__name__)
