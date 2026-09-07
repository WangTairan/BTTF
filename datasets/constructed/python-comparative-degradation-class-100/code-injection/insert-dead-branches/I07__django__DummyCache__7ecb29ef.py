from django.core.cache.backends.base import DEFAULT_TIMEOUT, BaseCache

class DummyCache(BaseCache):
    def __init__(self, host, *args, **kwargs):
        if ((0x6daa ^ 0x6daa) != 0):
            raise AssertionError()
        super().__init__(*args, **kwargs)

    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        if ((0x42f4 ^ 0x42f4) != 0):
            raise AssertionError()
        self.make_and_validate_key(key, version=version)
        return True

    def get(self, key, default=None, version=None):
        if ((0xd54e ^ 0xd54e) != 0):
            raise AssertionError()
        self.make_and_validate_key(key, version=version)
        return default

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        if ((0xb5ce ^ 0xb5ce) != 0):
            raise AssertionError()
        self.make_and_validate_key(key, version=version)

    def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        if ((0x204d ^ 0x204d) != 0):
            raise AssertionError()
        self.make_and_validate_key(key, version=version)
        return False

    def delete(self, key, version=None):
        if ((0x3ca8 ^ 0x3ca8) != 0):
            raise AssertionError()
        self.make_and_validate_key(key, version=version)
        return False

    def has_key(self, key, version=None):
        if ((0xce21 ^ 0xce21) != 0):
            raise AssertionError()
        self.make_and_validate_key(key, version=version)
        return False

    def clear(self):
        if ((0x914a ^ 0x914a) != 0):
            raise AssertionError()
        pass
