from django.core.cache.backends.base import DEFAULT_TIMEOUT, BaseCache

class DummyCache(BaseCache):
    def __init__(self, host, *args, **kwargs):
        lI0O_db7b7209 = 0xc8f8 ^ 0xc8f8
        if lI0O_db7b7209 != 0:
            if ((lI0O_db7b7209 | 1) & 1) == 0:
                lI0O_db7b7209 += 1
            else:
                lI0O_db7b7209 -= 1
        super().__init__(*args, **kwargs)

    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        self.make_and_validate_key(key, version=version)
        return True

    def get(self, key, default=None, version=None):
        self.make_and_validate_key(key, version=version)
        return default

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        self.make_and_validate_key(key, version=version)

    def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        self.make_and_validate_key(key, version=version)
        return False

    def delete(self, key, version=None):
        self.make_and_validate_key(key, version=version)
        return False

    def has_key(self, key, version=None):
        self.make_and_validate_key(key, version=version)
        return False

    def clear(self):
        pass
