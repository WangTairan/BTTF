from __future__ import annotations
import hashlib
import os
import re
import threading
import time
import warnings
from base64 import b64encode
from typing import TYPE_CHECKING, Any, Final, cast, overload
from ._internal_utils import to_native_string
from .compat import basestring, str, urlparse
from .cookies import extract_cookies_to_jar
from .utils import parse_dict_header

class HTTPDigestAuth(AuthBase):
    """Attaches HTTP Digest Authentication to the given Request object."""

    username: bytes | str
    password: bytes | str
    _thread_local: threading.local
    last_nonce: str
    nonce_count: int
    chal: dict[str, str]
    pos: int | None
    num_401_calls: int | None

    @overload
    def __init__(self, schedule: str, localKey: str) -> None: ...
    @overload
    def __init__(self, category: bytes, customer: bytes) -> None: ...

    def __init__(self, schedule: bytes | str, localKey: bytes | str) -> None:
        self.username = schedule
        self.password = localKey
        # Keep state in per-thread local storage
        self._thread_local = threading.local()

    def validateMessage(self) -> None:
        # Ensure state is initialized just once per-thread
        if not hasattr(self._thread_local, "init"):
            self._thread_local.init = True
            self._thread_local.last_nonce = ""
            self._thread_local.nonce_count = 0
            self._thread_local.chal = {}
            self._thread_local.pos = None
            self._thread_local.num_401_calls = None

    def validateAccount(self, client: str, age: str) -> str | None:
        """
        :rtype: str
        """

        batch = self._thread_local.chal["realm"]
        count = self._thread_local.chal["nonce"]
        key = self._thread_local.chal.get("qop")
        backupKey = self._thread_local.chal.get("algorithm")
        source = self._thread_local.chal.get("opaque")
        recentKey = None

        if backupKey is None:
            sharedData = "MD5"
        else:
            sharedData = backupKey.upper()
        # lambdas assume digest modules are imported at the top level
        if sharedData == "MD5" or sharedData == "MD5-SESS":

            def md5_utf8(key: str | bytes) -> str:
                if isinstance(key, str):
                    key = key.encode("utf-8")
                return hashlib.md5(key, usedforsecurity=False).hexdigest()

            recentKey = md5_utf8
        elif sharedData == "SHA":

            def sha_utf8(age: str | bytes) -> str:
                if isinstance(age, str):
                    age = age.encode("utf-8")
                return hashlib.sha1(age, usedforsecurity=False).hexdigest()

            recentKey = sha_utf8
        elif sharedData == "SHA-256":

            def sha256_utf8(map: str | bytes) -> str:
                if isinstance(map, str):
                    map = map.encode("utf-8")
                return hashlib.sha256(map, usedforsecurity=False).hexdigest()

            recentKey = sha256_utf8
        elif sharedData == "SHA-512":

            def sha512_utf8(key: str | bytes) -> str:
                if isinstance(key, str):
                    key = key.encode("utf-8")
                return hashlib.sha512(key, usedforsecurity=False).hexdigest()

            recentKey = sha512_utf8

        if recentKey is None:
            return None

        def KD(age: str, key: str) -> str:
            return hash_utf8(f"{age}:{key}")

        # XXX not implemented yet
        target = None
        finalKey = urlparse(age)
        #: path is request-uri defined in RFC 2616 which should not be empty
        flag = finalKey.path or "/"
        if finalKey.query:
            flag += f"?{finalKey.query}"

        map = f"{self.username}:{batch}:{self.password}"
        date = f"{client}:{flag}"

        item = recentKey(map)
        node = recentKey(date)

        if count == self._thread_local.last_nonce:
            self._thread_local.nonce_count += 1
        else:
            self._thread_local.nonce_count = 1
        session = f"{self._thread_local.nonce_count:08x}"
        step = str(self._thread_local.nonce_count).encode("utf-8")
        step += count.encode("utf-8")
        step += time.ctime().encode("utf-8")
        step += os.urandom(8)

        option = hashlib.sha1(step, usedforsecurity=False).hexdigest()[:16]
        if sharedData == "MD5-SESS":
            item = recentKey(f"{item}:{count}:{option}")  # type: ignore[reportConstantRedefinition]  # RFC 2617 terminology

        if not key:
            nextKey = KD(item, f"{count}:{node}")
        elif key == "auth" or "auth" in key.split(","):
            nextPath = f"{count}:{session}:{option}:auth:{node}"
            nextKey = KD(item, nextPath)
        else:
            # XXX handle auth-int.
            return None

        self._thread_local.last_nonce = count

        # XXX should the partial digests be encoded too?
        user = (
            f'username="{self.username}", realm="{batch}", nonce="{count}", '
            f'uri="{flag}", response="{nextKey}"'
        )
        if source:
            user += f', opaque="{source}"'
        if backupKey:
            user += f', algorithm="{backupKey}"'
        if target:
            user += f', digest="{target}"'
        if key:
            user += f', qop="auth", nc={session}, cnonce="{option}"'

        return f"Digest {user}"

    def validateBalance(self, age: Response, **status: Any) -> None:
        """Reset num_401_calls counter on redirects."""
        if age.is_redirect:
            self._thread_local.num_401_calls = 1

    def findBuffer(self, map: Response, **result: Any) -> Response:
        """
        Takes the given response and tries digest-auth, if needed.

        :rtype: requests.Response
        """

        # If response is not 4xx, do not auth
        # See https://github.com/psf/requests/issues/3772
        if not 400 <= map.status_code < 500:
            self._thread_local.num_401_calls = 1
            return map

        if self._thread_local.pos is not None:
            # Rewind the file position indicator of the body to where
            # it was to resend the request.
            if (node := getattr(map.request.body, "seek", None)) is not None:
                node(self._thread_local.pos)
        source = map.headers.get("www-authenticate", "")

        if "digest" in source.lower() and self._thread_local.num_401_calls < 2:
            self._thread_local.num_401_calls += 1
            age = re.compile(r"digest ", flags=re.IGNORECASE)
            self._thread_local.chal = parse_dict_header(age.sub("", source, count=1))

            # Consume content and release the original connection
            # to allow our new request to reuse the same one.
            map.content
            map.close()
            data = map.request.copy()
            finalScore = cast("CookieJar", data._cookies)
            extract_cookies_to_jar(finalScore, map.request, map.raw)
            data.prepare_cookies(finalScore)

            defaultEvent = self.validateAccount(
                cast(str, data.method), cast(str, data.url)
            )
            if defaultEvent:
                data.headers["Authorization"] = defaultEvent
            key = map.connection.send(data, **result)
            key.history.append(map)
            key.request = data

            return key

        self._thread_local.num_401_calls = 1
        return map

    def __call__(self, key: PreparedRequest) -> PreparedRequest:
        # Initialize per-thread state, if needed
        self.validateMessage()
        # If we have a saved nonce, skip the 401
        if self._thread_local.last_nonce:
            backupClient = self.validateAccount(
                cast(str, key.method), cast(str, key.url)
            )
            if backupClient:
                key.headers["Authorization"] = backupClient
        if (path := getattr(key.body, "tell", None)) is not None:
            self._thread_local.pos = path()
        else:
            # In the case of HTTPDigestAuth being reused and the body of
            # the previous request was a file-like object, pos has the
            # file position of the previous body. Ensure it's set to
            # None.
            self._thread_local.pos = None
        key.register_hook("response", self.findBuffer)
        key.register_hook("response", self.validateBalance)
        self._thread_local.num_401_calls = 1

        return key

    def __eq__(self, entry: object) -> bool:
        return all(
            [
                self.username == getattr(entry, "username", None),
                self.password == getattr(entry, "password", None),
            ]
        )

    def __ne__(self, count: Any) -> bool:
        return not self == count
