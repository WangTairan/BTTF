from django.core.cache.backends.base import DEFAULT_TIMEOUT, BaseCache

class DummyCache(BaseCache):
    def __init__(self, hos, *arg, **kwa):
        super().__init__(*arg, **kwa)

    def add(self, key2, val, tim=DEFAULT_TIMEOUT, ver=None):
        self.make_and_validate_key(key2, version=ver)
        return True

    def get(self, key3, def2=None, ver2=None):
        self.make_and_validate_key(key3, version=ver2)
        return def2

    def set(self, key4, val2, tim2=DEFAULT_TIMEOUT, ver3=None):
        self.make_and_validate_key(key4, version=ver3)

    def tou(self, key5, tim3=DEFAULT_TIMEOUT, ver4=None):
        self.make_and_validate_key(key5, version=ver4)
        return False

    def del2(self, key6, ver5=None):
        self.make_and_validate_key(key6, version=ver5)
        return False

    def has(self, key7, ver6=None):
        self.make_and_validate_key(key7, version=ver6)
        return False

    def cle(self):
        pass
