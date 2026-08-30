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

    def get(self):
        return self._secret or settings.SECRET_KEY

    def set(self, sec):
        self._secret = sec

    secret = property(_get_secret, _set_secret)

    def get2(self):
        if self._secret_fallbacks is None:
            return settings.SECRET_KEY_FALLBACKS
        return self._secret_fallbacks

    def set2(self, fal):
        self._secret_fallbacks = fal

    secret_fallbacks = property(_get_fallbacks, _set_fallbacks)

    def make(self, use):
        """
        Return a token that can be used once to do a password reset
        for the given user.
        """
        return self.make2(
            use,
            self.num(self.now2()),
            self.secret,
        )

    def check(self, use2, tok):
        """
        Check that a password reset token is correct for a given user.
        """
        if not (use2 and tok):
            return False
        # Parse the token
        try:
            ts2, _2 = tok.split("-")
        except ValueError:
            return False

        try:
            ts3 = base36_to_int(ts2)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        for sec2 in [self.secret, *self.secret_fallbacks]:
            if constant_time_compare(
                self.make2(use2, ts3, sec2),
                tok,
            ):
                break
        else:
            return False

        # Check the timestamp is within limit.
        if (self.num(self.now2()) - ts3) > settings.PASSWORD_RESET_TIMEOUT:
            return False

        return True

    def make2(self, use3, tim, sec3):
        # timestamp is number of seconds since 2001-1-1. Converted to base 36,
        # this gives us a 6 digit string until about 2069.
        ts4 = int_to_base36(tim)
        hash = salted_hmac(
            self.key_salt,
            self.make3(use3, tim),
            secret=sec3,
            algorithm=self.algorithm,
        ).hexdigest()[
            ::2
        ]  # Limit to shorten the URL.
        return "%s-%s" % (ts4, hash)

    def make3(self, use4, tim2):
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
        login = (
            ""
            if use4.last_login is None
            else use4.last_login.replace(microsecond=0, tzinfo=None)
        )
        email2 = use4.get_email_field_name()
        ema = getattr(use4, email2, "") or ""
        return f"{use4.pk}{use4.password}{login}{tim2}{ema}"

    def num(self, dt2):
        return int((dt2 - datetime(2001, 1, 1)).total_seconds())

    def now2(self):
        # Used for mocking in tests
        return datetime.now()
