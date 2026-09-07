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
    def __init__(self, use: str, pas: str) -> None: ...
    @overload
    def __init__(self, use2: bytes, pas2: bytes) -> None: ...

    def __init__(self, use3: bytes | str, pas3: bytes | str) -> None:
        self.username = use3
        self.password = pas3
        # Keep state in per-thread local storage
        self._thread_local = threading.local()

    def init2(self) -> None:
        # Ensure state is initialized just once per-thread
        if not hasattr(self._thread_local, "init"):
            self._thread_local.init = True
            self._thread_local.last_nonce = ""
            self._thread_local.nonce_count = 0
            self._thread_local.chal = {}
            self._thread_local.pos = None
            self._thread_local.num_401_calls = None

    def build(self, met: str, url2: str) -> str | None:
        """
        :rtype: str
        """

        rea = self._thread_local.chal["realm"]
        non = self._thread_local.chal["nonce"]
        qop2 = self._thread_local.chal.get("qop")
        alg = self._thread_local.chal.get("algorithm")
        opa = self._thread_local.chal.get("opaque")
        hash = None

        if alg is None:
            alg2 = "MD5"
        else:
            alg2 = alg.upper()
        # lambdas assume digest modules are imported at the top level
        if alg2 == "MD5" or alg2 == "MD5-SESS":

            def md5_utf8(x2: str | bytes) -> str:
                if isinstance(x2, str):
                    x2 = x2.encode("utf-8")
                return hashlib.md5(x2, usedforsecurity=False).hexdigest()

            hash = md5_utf8
        elif alg2 == "SHA":

            def sha_utf8(x3: str | bytes) -> str:
                if isinstance(x3, str):
                    x3 = x3.encode("utf-8")
                return hashlib.sha1(x3, usedforsecurity=False).hexdigest()

            hash = sha_utf8
        elif alg2 == "SHA-256":

            def sha256_utf8(x4: str | bytes) -> str:
                if isinstance(x4, str):
                    x4 = x4.encode("utf-8")
                return hashlib.sha256(x4, usedforsecurity=False).hexdigest()

            hash = sha256_utf8
        elif alg2 == "SHA-512":

            def sha512_utf8(x5: str | bytes) -> str:
                if isinstance(x5, str):
                    x5 = x5.encode("utf-8")
                return hashlib.sha512(x5, usedforsecurity=False).hexdigest()

            hash = sha512_utf8

        if hash is None:
            return None

        def KD(s3: str, d2: str) -> str:
            return hash_utf8(f"{s3}:{d2}")

        # XXX not implemented yet
        ent = None
        p = urlparse(url2)
        #: path is request-uri defined in RFC 2616 which should not be empty
        pat2 = p.path or "/"
        if p.query:
            pat2 += f"?{p.query}"

        a1 = f"{self.username}:{rea}:{self.password}"
        a2 = f"{met}:{pat2}"

        hA1 = hash(a1)
        hA2 = hash(a2)

        if non == self._thread_local.last_nonce:
            self._thread_local.nonce_count += 1
        else:
            self._thread_local.nonce_count = 1
        ncv = f"{self._thread_local.nonce_count:08x}"
        s2 = str(self._thread_local.nonce_count).encode("utf-8")
        s2 += non.encode("utf-8")
        s2 += time.ctime().encode("utf-8")
        s2 += os.urandom(8)

        cno = hashlib.sha1(s2, usedforsecurity=False).hexdigest()[:16]
        if alg2 == "MD5-SESS":
            hA1 = hash(f"{hA1}:{non}:{cno}")  # type: ignore[reportConstantRedefinition]  # RFC 2617 terminology

        if not qop2:
            res = KD(hA1, f"{non}:{hA2}")
        elif qop2 == "auth" or "auth" in qop2.split(","):
            non2 = f"{non}:{ncv}:{cno}:auth:{hA2}"
            res = KD(hA1, non2)
        else:
            # XXX handle auth-int.
            return None

        self._thread_local.last_nonce = non

        # XXX should the partial digests be encoded too?
        bas = (
            f'username="{self.username}", realm="{rea}", nonce="{non}", '
            f'uri="{pat2}", response="{res}"'
        )
        if opa:
            bas += f', opaque="{opa}"'
        if alg:
            bas += f', algorithm="{alg}"'
        if ent:
            bas += f', digest="{ent}"'
        if qop2:
            bas += f', qop="auth", nc={ncv}, cnonce="{cno}"'

        return f"Digest {bas}"

    def handle(self, r2: Response, **kwa: Any) -> None:
        """Reset num_401_calls counter on redirects."""
        if r2.is_redirect:
            self._thread_local.num_401_calls = 1

    def handle2(self, r3: Response, **kwa2: Any) -> Response:
        """
        Takes the given response and tries digest-auth, if needed.

        :rtype: requests.Response
        """

        # If response is not 4xx, do not auth
        # See https://github.com/psf/requests/issues/3772
        if not 400 <= r3.status_code < 500:
            self._thread_local.num_401_calls = 1
            return r3

        if self._thread_local.pos is not None:
            # Rewind the file position indicator of the body to where
            # it was to resend the request.
            if (see := getattr(r3.request.body, "seek", None)) is not None:
                see(self._thread_local.pos)
        s4 = r3.headers.get("www-authenticate", "")

        if "digest" in s4.lower() and self._thread_local.num_401_calls < 2:
            self._thread_local.num_401_calls += 1
            pat3 = re.compile(r"digest ", flags=re.IGNORECASE)
            self._thread_local.chal = parse_dict_header(pat3.sub("", s4, count=1))

            # Consume content and release the original connection
            # to allow our new request to reuse the same one.
            r3.content
            r3.close()
            pre = r3.request.copy()
            cookie = cast("CookieJar", pre._cookies)
            extract_cookies_to_jar(cookie, r3.request, r3.raw)
            pre.prepare_cookies(cookie)

            digest = self.build(
                cast(str, pre.method), cast(str, pre.url)
            )
            if digest:
                pre.headers["Authorization"] = digest
            r4 = r3.connection.send(pre, **kwa2)
            r4.history.append(r3)
            r4.request = pre

            return r4

        self._thread_local.num_401_calls = 1
        return r3

    def __call__(self, r5: PreparedRequest) -> PreparedRequest:
        # Initialize per-thread state, if needed
        self.init2()
        # If we have a saved nonce, skip the 401
        if self._thread_local.last_nonce:
            digest2 = self.build(
                cast(str, r5.method), cast(str, r5.url)
            )
            if digest2:
                r5.headers["Authorization"] = digest2
        if (tel := getattr(r5.body, "tell", None)) is not None:
            self._thread_local.pos = tel()
        else:
            # In the case of HTTPDigestAuth being reused and the body of
            # the previous request was a file-like object, pos has the
            # file position of the previous body. Ensure it's set to
            # None.
            self._thread_local.pos = None
        r5.register_hook("response", self.handle2)
        r5.register_hook("response", self.handle)
        self._thread_local.num_401_calls = 1

        return r5

    def __eq__(self, oth: object) -> bool:
        return all(
            [
                self.username == getattr(oth, "username", None),
                self.password == getattr(oth, "password", None),
            ]
        )

    def __ne__(self, oth2: Any) -> bool:
        return not self == oth2
