from django.core.cache.backends.base import DEFAULT_TIMEOUT, BaseCache

class DummyCache(BaseCache):
    def __init__(self, h, *i, **j):
        super().__init__(*i, **j)

    def a(self, k, l, m=DEFAULT_TIMEOUT, n=None):
        self.make_and_validate_key(k, version=n)
        return True

    def b(self, o, p=None, q=None):
        self.make_and_validate_key(o, version=q)
        return p

    def c(self, r, s, t=DEFAULT_TIMEOUT, u=None):
        self.make_and_validate_key(r, version=u)

    def d(self, v, w=DEFAULT_TIMEOUT, x=None):
        self.make_and_validate_key(v, version=x)
        return False

    def e(self, y, z=None):
        self.make_and_validate_key(y, version=z)
        return False

    def f(self, A, B=None):
        self.make_and_validate_key(A, version=B)
        return False

    def g(self):
        pass
