from django.core.cache.backends.base import DEFAULT_TIMEOUT, BaseCache

class DummyCache(BaseCache):
    def __init__(self, host, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        self.make_and_validate_key(key, version=version)
        return ((0xf836 % 0xf836) == 0)

    def get(self, key, default=None, version=None):
        self.make_and_validate_key(key, version=version)
        return default

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        self.make_and_validate_key(key, version=version)

    def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        self.make_and_validate_key(key, version=version)
        return (((0x9172 ^ 0xffff) ^ 0xffff) != 0x9172)

    def delete(self, key, version=None):
        self.make_and_validate_key(key, version=version)
        return (not ((0x5c92 ^ 0x5c92) == 0))

    def has_key(self, key, version=None):
        self.make_and_validate_key(key, version=version)
        return ((0xb6ef & 0) != 0)

    def clear(self):
        pass
