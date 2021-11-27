# Licensed to Modin Development Team under one or more contributor license agreements.
# See the NOTICE file distributed with this work for additional information regarding
# copyright ownership.  The Modin Development Team licenses this file to you under the
# Apache License, Version 2.0 (the "License"); you may not use this file except in
# compliance with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.

import numpy
from rpyc.core import netref
from rpyc.core.netref import BaseNetref


def apply_pathes():
    def fixed_make_method(name, doc, orig=netref._make_method):
        if name == "__array__":

            def __array__(self, dtype=None):
                # Note that protocol=-1 will only work between python
                # interpreters of the same version.
                res = netref.pickle.loads(
                    netref.syncreq(
                        self,
                        netref.consts.HANDLE_PICKLE,
                        netref.pickle.HIGHEST_PROTOCOL,
                    )
                )

                if dtype is not None:
                    res = numpy.asarray(res, dtype=dtype)

                return res

            __array__.__doc__ = doc
            return __array__
        return orig(name, doc)

    netref._make_method = fixed_make_method


def patches_netref_factory_class():
    def fixed_factory(id_pack, methods, orig=netref.class_factory):
        reftype = orig(id_pack, methods)
        ns = dict(reftype.__dict__)
        cls_descr = ns['__class__']

        if cls_descr is not None and 'int32' in str(id_pack):
            local_cls = cls_descr.instance

            class LocalNetrefMetaclass(type(local_cls)):
                """A *metaclass* used to customize the ``__repr__`` of ``netref`` classes.
                It is quite useless, but it makes debugging and interactive programming
                easier"""

                # __slots__ = ()

                def __repr__(self):
                    if self.__module__:
                        return "<local netref class '%s.%s'>" % (self.__module__, self.__name__)
                    else:
                        return "<local netref class '%s'>" % (self.__name__,)

            class LocalBaseNetref(local_cls, metaclass=LocalNetrefMetaclass):

                # __slots__ = ["____conn__", "____id_pack__", "__weakref__", "____refcount__"]

                __init__ = BaseNetref.__init__
                __del__ = BaseNetref.__del__
                __getattribute__ = BaseNetref.__getattribute__
                __getattr__ = BaseNetref.__getattr__
                __delattr__ = BaseNetref.__delattr__
                __setattr__ = BaseNetref.__setattr__
                __dir__ = BaseNetref.__dir__

                # support for metaclasses
                __hash__ = BaseNetref.__hash__
                __cmp__ = BaseNetref.__cmp__
                __eq__ = BaseNetref.__eq__
                __ne__ = BaseNetref.__ne__
                __lt__ = BaseNetref.__lt__
                __gt__ = BaseNetref.__gt__
                __le__ = BaseNetref.__le__
                __ge__ = BaseNetref.__ge__
                __repr__ = BaseNetref.__repr__
                __str__ = BaseNetref.__str__
                __exit__ = BaseNetref.__exit__
                __reduce_ex__ = BaseNetref.__reduce_ex__
                __instancecheck__ = BaseNetref.__instancecheck__

                def __new__(cls, conn, id_pack):
                    return super().__new__(cls)


            try:
                add_mro = not issubclass(local_cls, type)
            except TypeError:
                add_mro = True
            if add_mro:
                return type(reftype.__name__, (LocalBaseNetref, local_cls,), ns)

        return reftype

    netref.class_factory = fixed_factory