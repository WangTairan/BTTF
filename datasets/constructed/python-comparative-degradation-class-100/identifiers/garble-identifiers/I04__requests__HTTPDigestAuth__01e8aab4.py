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
    def __init__(self, f: str, g: str) -> None: ...
    @overload
    def __init__(self, h: bytes, i: bytes) -> None: ...

    def __init__(self, j: bytes | str, k: bytes | str) -> None:
        self.username = j
        self.password = k
        # Keep state in per-thread local storage
        self._thread_local = threading.local()

    def a(self) -> None:
        # Ensure state is initialized just once per-thread
        if not hasattr(self._thread_local, "init"):
            self._thread_local.init = True
            self._thread_local.last_nonce = ""
            self._thread_local.nonce_count = 0
            self._thread_local.chal = {}
            self._thread_local.pos = None
            self._thread_local.num_401_calls = None

    def b(self, l: str, m: str) -> str | None:
        """
        :rtype: str
        """

        n = self._thread_local.chal["realm"]
        o = self._thread_local.chal["nonce"]
        p = self._thread_local.chal.get("qop")
        q = self._thread_local.chal.get("algorithm")
        t = self._thread_local.chal.get("opaque")
        u = None

        if q is None:
            v = "MD5"
        else:
            v = q.upper()
        # lambdas assume digest modules are imported at the top level
        if v == "MD5" or v == "MD5-SESS":

            def md5_utf8(K: str | bytes) -> str:
                if isinstance(K, str):
                    K = K.encode("utf-8")
                return hashlib.md5(K, usedforsecurity=False).hexdigest()

            u = md5_utf8
        elif v == "SHA":

            def sha_utf8(L: str | bytes) -> str:
                if isinstance(L, str):
                    L = L.encode("utf-8")
                return hashlib.sha1(L, usedforsecurity=False).hexdigest()

            u = sha_utf8
        elif v == "SHA-256":

            def sha256_utf8(M: str | bytes) -> str:
                if isinstance(M, str):
                    M = M.encode("utf-8")
                return hashlib.sha256(M, usedforsecurity=False).hexdigest()

            u = sha256_utf8
        elif v == "SHA-512":

            def sha512_utf8(N: str | bytes) -> str:
                if isinstance(N, str):
                    N = N.encode("utf-8")
                return hashlib.sha512(N, usedforsecurity=False).hexdigest()

            u = sha512_utf8

        if u is None:
            return None

        def KD(O: str, P: str) -> str:
            return hash_utf8(f"{O}:{P}")

        # XXX not implemented yet
        w = None
        y = urlparse(m)
        #: path is request-uri defined in RFC 2616 which should not be empty
        z = y.path or "/"
        if y.query:
            z += f"?{y.query}"

        A = f"{self.username}:{n}:{self.password}"
        B = f"{l}:{z}"

        C = u(A)
        D = u(B)

        if o == self._thread_local.last_nonce:
            self._thread_local.nonce_count += 1
        else:
            self._thread_local.nonce_count = 1
        E = f"{self._thread_local.nonce_count:08x}"
        F = str(self._thread_local.nonce_count).encode("utf-8")
        F += o.encode("utf-8")
        F += time.ctime().encode("utf-8")
        F += os.urandom(8)

        G = hashlib.sha1(F, usedforsecurity=False).hexdigest()[:16]
        if v == "MD5-SESS":
            C = u(f"{C}:{o}:{G}")  # type: ignore[reportConstantRedefinition]  # RFC 2617 terminology

        if not p:
            H = KD(C, f"{o}:{D}")
        elif p == "auth" or "auth" in p.split(","):
            I = f"{o}:{E}:{G}:auth:{D}"
            H = KD(C, I)
        else:
            # XXX handle auth-int.
            return None

        self._thread_local.last_nonce = o

        # XXX should the partial digests be encoded too?
        J = (
            f'username="{self.username}", realm="{n}", nonce="{o}", '
            f'uri="{z}", response="{H}"'
        )
        if t:
            J += f', opaque="{t}"'
        if q:
            J += f', algorithm="{q}"'
        if w:
            J += f', digest="{w}"'
        if p:
            J += f', qop="auth", nc={E}, cnonce="{G}"'

        return f"Digest {J}"

    def c(self, Q: Response, **R: Any) -> None:
        """Reset num_401_calls counter on redirects."""
        if Q.is_redirect:
            self._thread_local.num_401_calls = 1

    def e(self, S: Response, **T: Any) -> Response:
        """
        Takes the given response and tries digest-auth, if needed.

        :rtype: requests.Response
        """

        # If response is not 4xx, do not auth
        # See https://github.com/psf/requests/issues/3772
        if not 400 <= S.status_code < 500:
            self._thread_local.num_401_calls = 1
            return S

        if self._thread_local.pos is not None:
            # Rewind the file position indicator of the body to where
            # it was to resend the request.
            if (U := getattr(S.request.body, "seek", None)) is not None:
                U(self._thread_local.pos)
        V = S.headers.get("www-authenticate", "")

        if "digest" in V.lower() and self._thread_local.num_401_calls < 2:
            self._thread_local.num_401_calls += 1
            W = re.compile(r"digest ", flags=re.IGNORECASE)
            self._thread_local.chal = parse_dict_header(W.sub("", V, count=1))

            # Consume content and release the original connection
            # to allow our new request to reuse the same one.
            S.content
            S.close()
            X = S.request.copy()
            Y = cast("CookieJar", X._cookies)
            extract_cookies_to_jar(Y, S.request, S.raw)
            X.prepare_cookies(Y)

            Z = self.b(
                cast(str, X.method), cast(str, X.url)
            )
            if Z:
                X.headers["Authorization"] = Z
            aa = S.connection.send(X, **T)
            aa.history.append(S)
            aa.request = X

            return aa

        self._thread_local.num_401_calls = 1
        return S

    def __call__(self, ab: PreparedRequest) -> PreparedRequest:
        # Initialize per-thread state, if needed
        self.a()
        # If we have a saved nonce, skip the 401
        if self._thread_local.last_nonce:
            ac = self.b(
                cast(str, ab.method), cast(str, ab.url)
            )
            if ac:
                ab.headers["Authorization"] = ac
        if (ad := getattr(ab.body, "tell", None)) is not None:
            self._thread_local.pos = ad()
        else:
            # In the case of HTTPDigestAuth being reused and the body of
            # the previous request was a file-like object, pos has the
            # file position of the previous body. Ensure it's set to
            # None.
            self._thread_local.pos = None
        ab.register_hook("response", self.e)
        ab.register_hook("response", self.c)
        self._thread_local.num_401_calls = 1

        return ab

    def __eq__(self, ae: object) -> bool:
        return all(
            [
                self.username == getattr(ae, "username", None),
                self.password == getattr(ae, "password", None),
            ]
        )

    def __ne__(self, af: Any) -> bool:
        return not self == af
