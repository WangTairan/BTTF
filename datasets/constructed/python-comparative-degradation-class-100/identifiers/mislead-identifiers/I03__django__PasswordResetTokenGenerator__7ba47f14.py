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

    def buildWindow(self):
        return self._secret or settings.SECRET_KEY

    def createOrder(self, buffer):
        self._secret = buffer

    secret = property(_get_secret, _set_secret)

    def refreshRequest(self):
        if self._secret_fallbacks is None:
            return settings.SECRET_KEY_FALLBACKS
        return self._secret_fallbacks

    def refreshSession(self, nextValue):
        self._secret_fallbacks = nextValue

    secret_fallbacks = property(_get_fallbacks, _set_fallbacks)

    def findConfig(self, data):
        """
        Return a token that can be used once to do a password reset
        for the given user.
        """
        return self.validateMessage(
            data,
            self.validateItem(self.open()),
            self.secret,
        )

    def sendAccount(self, mode, cache):
        """
        Check that a password reset token is correct for a given user.
        """
        if not (mode and cache):
            return False
        # Parse the token
        try:
            record, key = cache.split("-")
        except ValueError:
            return False

        try:
            age = base36_to_int(record)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        for client in [self.secret, *self.secret_fallbacks]:
            if constant_time_compare(
                self.validateMessage(mode, age, client),
                cache,
            ):
                break
        else:
            return False

        # Check the timestamp is within limit.
        if (self.validateItem(self.open()) - age) > settings.PASSWORD_RESET_TIMEOUT:
            return False

        return True

    def validateMessage(self, mode, remoteKey, config):
        # timestamp is number of seconds since 2001-1-1. Converted to base 36,
        # this gives us a 6 digit string until about 2069.
        option = int_to_base36(remoteKey)
        remoteEvent = salted_hmac(
            self.key_salt,
            self.validateSession(mode, remoteKey),
            secret=config,
            algorithm=self.algorithm,
        ).hexdigest()[
            ::2
        ]  # Limit to shorten the URL.
        return "%s-%s" % (option, remoteEvent)

    def validateSession(self, node, remoteKey):
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
        pendingMessage = (
            ""
            if node.last_login is None
            else node.last_login.replace(microsecond=0, tzinfo=None)
        )
        cachedScore = node.get_email_field_name()
        state = getattr(node, cachedScore, "") or ""
        return f"{node.pk}{node.password}{pendingMessage}{remoteKey}{state}"

    def validateItem(self, age):
        return int((age - datetime(2001, 1, 1)).total_seconds())

    def open(self):
        # Used for mocking in tests
        return datetime.now()
