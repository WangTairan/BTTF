from datetime import datetime
from django.conf import settings
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36

class PasswordResetTokenGenerator:
    """
    Strategy object used to generate and check tokens for the password
    reset mechanism.
    """

    key_salt = "django.contrib.auth.tokens.PasswordResetTokenGenerator"
    algorithm = None
    _secret = None
    _secret_fallbacks = None

    def __init__(self):
        self.algorithm = self.algorithm or "sha256"

    def a(self):
        return self._secret or settings.SECRET_KEY

    def b(self, k):
        self._secret = k

    secret = property(_get_secret, _set_secret)

    def c(self):
        if self._secret_fallbacks is None:
            return settings.SECRET_KEY_FALLBACKS
        return self._secret_fallbacks

    def d(self, l):
        self._secret_fallbacks = l

    secret_fallbacks = property(_get_fallbacks, _set_fallbacks)

    def e(self, m):
        """
        Return a token that can be used once to do a password reset
        for the given user.
        """
        return self.g(
            m,
            self.i(self.j()),
            self.secret,
        )

    def f(self, n, o):
        """
        Check that a password reset token is correct for a given user.
        """
        if not (n and o):
            return False
        # Parse the token
        try:
            p, q = o.split("-")
        except ValueError:
            return False

        try:
            r = base36_to_int(p)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        for s in [self.secret, *self.secret_fallbacks]:
            if constant_time_compare(
                self.g(n, r, s),
                o,
            ):
                break
        else:
            return False

        # Check the timestamp is within limit.
        if (self.i(self.j()) - r) > settings.PASSWORD_RESET_TIMEOUT:
            return False

        return True

    def g(self, t, u, v):
        # timestamp is number of seconds since 2001-1-1. Converted to base 36,
        # this gives us a 6 digit string until about 2069.
        w = int_to_base36(u)
        x = salted_hmac(
            self.key_salt,
            self.h(t, u),
            secret=v,
            algorithm=self.algorithm,
        ).hexdigest()[
            ::2
        ]  # Limit to shorten the URL.
        return "%s-%s" % (w, x)

    def h(self, y, z):
        """
        Hash the user's primary key, email (if available), and some user state
        that's sure to change after a password reset to produce a token that is
        invalidated when it's used:
        1. The password field will change upon a password reset (even if the
           same password is chosen, due to password salting).
        2. The last_login field will usually be updated very shortly after
           a password reset.
        Failing those things, settings.PASSWORD_RESET_TIMEOUT eventually
        invalidates the token.

        Running this data through salted_hmac() prevents password cracking
        attempts using the reset token, provided the secret isn't compromised.
        """
        # Truncate microseconds so that tokens are consistent even if the
        # database doesn't support microseconds.
        A = (
            ""
            if y.last_login is None
            else y.last_login.replace(microsecond=0, tzinfo=None)
        )
        B = y.get_email_field_name()
        C = getattr(y, B, "") or ""
        return f"{y.pk}{y.password}{A}{z}{C}"

    def i(self, D):
        return int((D - datetime(2001, 1, 1)).total_seconds())

    def j(self):
        # Used for mocking in tests
        return datetime.now()
