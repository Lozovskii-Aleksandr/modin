# ReadMe.md

Here is the result of the investigation of the error `TypeError - Cannot interpret 'dtype('int32')'as a data type`.

## Description of the problem

Link to the corresponding `issue` on GitHub:

[issue](https://github.com/modin-project/modin/issues/3348)

Initially there was an error [TypeError - issubclass() arg 1 must be a class](https://github.com/modin-project/modin/issues/3280). In version `modin 0.10.0`, the error is reproduced. In version `modin 0.10.1` it is not reproduced, but the test crashes with another error. There is a suspicion that someone broke something or fixed it. But since the error did not appear in the tests that worked, then most likely the bug was fixed in the update. In this update, `modin` has updated `pandas`.

## Notes on the problem

### Running the test

```shell
set MODIN_EXPERIMENTAL=1
set MODIN_ENGINE=Python
python -m pytest --capture=no --simulate-cloud=normal modin/pandas/test/test_series.py::test_callable_key_in_getitem[int_data]
```

### There used to be such an error (before modin 0.10.1)

```shell
modin\pandas\test\utils.py:540: in df_equals
    assert_series_equal(df1, df2, check_dtype=False, check_series_type=False)
C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\pandas\_testing.py:744: in _check_types
    assert_attr_equal("dtype", left, right, obj=obj)
C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\pandas\core\dtypes\inference.py:68: in is_number
    return isinstance(obj, (Number, np.number))
C:\Users\alozovsk\Anaconda3\envs\modin\lib\abc.py:98: in __instancecheck__
    return _abc_instancecheck(cls, instance)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

cls = <class 'numbers.Number'>, subclass = <class 'numpy.dtype[int64]'>

    def __subclasscheck__(cls, subclass):
        """Override for issubclass(subclass, cls)."""
>       return _abc_subclasscheck(cls, subclass)
E       TypeError: issubclass() arg 1 must be a class

C:\Users\alozovsk\Anaconda3\envs\modin\lib\abc.py:102: TypeError
```

### Remote traceback

```shell
E  ========= Remote Traceback (1) =========
E  Traceback (most recent call last):
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 326, in _dispatch_request
E      res = self._HANDLERS[handler](self, *args)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 614, in _handle_call
E      return obj(*args, **dict(kwargs))
E    File "C:\prog\modin\modin\pandas\series.py", line 150, in __init__
E      pandas.Series(
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\pandas\core\series.py", line 443, in __init__
E      data = SingleBlockManager.from_array(data, index)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\pandas\core\internals\managers.py", line 1574, in from_array
E      block = new_block(array, placement=slice(0, len(index)), ndim=1)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\pandas\core\internals\blocks.py", line 1935, in new_block
E      klass = get_block_type(values, values.dtype)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\pandas\core\internals\blocks.py", line 1900, in get_block_type
E      dtype = cast(np.dtype, pandas_dtype(dtype) if dtype else values.dtype)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\pandas\core\dtypes\common.py", line 1776, in pandas_dtype
E      npdtype = np.dtype(dtype)
E  TypeError: Cannot interpret 'dtype('int32')' as a data type

C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\async_.py:102: TypeError
```

### Difference with local version

If you run it locally, and follow how the code behaves at a similar moment in `modin in the cloud`, you can see that differences begin there. In local mode, the condition `isinstance(dtype, (np.dtype, ExtensionDtype))` is triggered for `dtype('int32')`:

[Ссылка на GitHub](https://github.com/pandas-dev/pandas/blob/master/pandas/core/dtypes/common.py#L1762-L1763)

In remote mode, this condition does not work, because a proxy object arrives that is not the heir of these types.

### Need to change the behavior of `__isinstancecheck__`

Suggested to make a wrapper for `rpyc.core.netref.class_factory`:

```py
def fixed_factory(id_pack, methods):
    reftype = class_factory(id_pack, methods)
    ns = dict(reftype.__dict__)
    cls_descr = ns['__class__']
    if cls_descr is not None:
        local_cls = cls_descr.instance
        try:
            add_mro = not issubclass(local_cls, type)
        except TypeError:
            add_mro = True
        if add_mro:
            return type(reftype.__name__, reftype.__bases__ + (local_cls,), ns)
    return reftype
```

But the wrapper in its pure form falls with an error (several slots):

```shell
TypeError: multiple bases have instance lay-out conflict
```

It is necessary for objects in `__class__` to specify not only `BaseNetref`, but also those types that should pass in `isinstance()`.

To do this, for each proxy object that has a local variant, generate its own metaclass, which is inherited from the metaclass of the local object, and then generate a `BaseNetref` to it.

To do this, copy the `BaseNetref` class and the `NetrefMetaclass` metaclass from `rpyc.core.netref.class_factory` into the wrapper, call them local. We remove the `__slots__` from them, which are in the original.

As a result, we get an infinite loop. With this conclusion:

```shell
E  ========= Remote Traceback (2) =========
E  Traceback (most recent call last):
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 342, in _dispatch_request
E      res = self._HANDLERS[handler](self, *args)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 646, in _handle_getattr
E      return self._access_attr(obj, name, (), "_rpyc_getattr", "allow_getattr", getattr)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 568, in _access_attr
E      return accessor(obj, name, *args)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\netref.py", line 162, in __getattribute__
E      return syncreq(self, consts.HANDLE_GETATTR, name)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\netref.py", line 76, in syncreq
E      return conn.sync_request(handler, proxy, *args)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 500, in sync_request
E      return self.async_request(handler, *args, timeout=timeout).value
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\async_.py", line 102, in value
E      raise self._obj
E  _get_exception_class.<locals>.Derived: maximum recursion depth exceeded while calling a Python object

E ========= Remote Traceback (1) =========
E  Traceback (most recent call last):
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 342, in _dispatch_request
E      res = self._HANDLERS[handler](self, *args)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 646, in _handle_getattr
E      return self._access_attr(obj, name, (), "_rpyc_getattr", "allow_getattr", getattr)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 568, in _access_attr
E      return accessor(obj, name, *args)
E    File "C:\prog\modin\modin\experimental\cloud\rpyc_proxy.py", line 216, in __getattribute__
E      return orig_getattribute(this, name)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\netref.py", line 162, in __getattribute__
E      return syncreq(self, consts.HANDLE_GETATTR, name)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\netref.py", line 76, in syncreq
E      return conn.sync_request(handler, proxy, *args)
E    File "C:\prog\modin\modin\experimental\cloud\rpyc_proxy.py", line 166, in sync_request
E      return super().sync_request(handler, *args)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 500, in sync_request
E      return self.async_request(handler, *args, timeout=timeout).value
E    File "C:\prog\modin\modin\experimental\cloud\rpyc_proxy.py", line 184, in async_request
E      return super().async_request(handler, *args, **kw)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 524, in async_request
E      self._async_request(handler, args, res)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 506, in _async_request
E      self._send(consts.MSG_REQUEST, seq, (handler, self._box(args)))
E    File "C:\prog\modin\modin\experimental\cloud\rpyc_proxy.py", line 270, in _box
E      return super()._box(obj)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 274, in _box
E      tmp = tuple(self._box(item) for item in obj)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 274, in <genexpr>
E      tmp = tuple(self._box(item) for item in obj)
E    File "C:\prog\modin\modin\experimental\cloud\rpyc_proxy.py", line 270, in _box
E      return super()._box(obj)
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 271, in _box
E      if brine.dumpable(obj):
E    File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\brine.py", line 404, in dumpable
E      if type(obj) in simple_types:
E  RecursionError: maximum recursion depth exceeded while calling a Python object

C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\async_.py:102: RecursionError
```

You can limit the use of the patch only for the specified classes for now. For example, for all that contain `int32`. In the future, it can be expanded for the whole `numpy`. In this case, the type `np.int32` will be considered separately.

To do this, in the wrapper, change the line `if cls_descr is not None:` on `if cls_descr is not None and 'int32' in str(id_pack):`.

From an infinite loop we came to the problem 'TypeError: function takes at most 1 argument (2 given)`:

```shell
E   ========= Remote Traceback (1) =========
...
E     File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 423, in serve
E       self._dispatch(data)
E     File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 382, in _dispatch
E       obj = self._unbox(args)
E     File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 309, in _unbox
E       proxy = self._netref_factory(id_pack)
E     File "C:\Users\alozovsk\Anaconda3\envs\modin\lib\site-packages\rpyc\core\protocol.py", line 336, in _netref_factory
E       return cls(self, id_pack)
E   TypeError: function takes at most 1 argument (2 given)
```

The `cls` variable is the class that the `netref.class_factory` function returns, and is then modified by the `fixed_factory` wrapper. Here `cls` has redefined the constructor. Instead of the constructor from `BaseNetref`, the constructor from `numpy.int32` is used:

```shell
# Without additional logic
(Pdb) cls
<netref class 'rpyc.core.netref.type'>

(Pdb) cls()
*** TypeError: __init__() missing 2 required positional arguments: 'conn' and 'id_pack'

(Pdb) type(cls)
<class 'rpyc.core.netref.NetrefMetaclass'>

---

# With edits for local objects
(Pdb) cls
<local netref class 'rpyc.core.netref.type'>

(Pdb) cls()
0

(Pdb) type(cls)
<class 'modin.experimental.cloud.rpyc_patches.aaa.<locals>.fixed_factory.<locals>.LocalNetrefMetaclass'>
```

The problem was solved by overriding the `__new__` method in `LocalBaseNetref` in the `rpyc_patches` file:

```py
def __new__(cls, conn, id_pack):
    return super().__new__(cls)
```

This in turn led to the problem that `weakref` does not work for wrapper-created objects. It shouldn't work for `np.int32`, but apart from that it doesn't work for its heirs either. And the wrapper just crosses `BaseNetref` and `np.int32`, which is why an error occurs.

This turned out to be a dead-end problem, which is not clear how to solve. We decided to postpone it until better times, since it is not clear how to correct it correctly.
