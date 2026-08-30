import re
from urllib.parse import urlsplit
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import MailerDoesNotExist, mail_managers, mailers
from django.http import HttpResponsePermanentRedirect
from django.middleware import MiddlewareMixin
from django.urls import is_valid_path
from django.utils.http import escape_leading_slashes

class CommonMiddleware(MiddlewareMixin):
    """
    "Common" middleware for taking care of some basic operations:

        - Forbid access to User-Agents in settings.DISALLOWED_USER_AGENTS

        - URL rewriting: Based on the APPEND_SLASH and PREPEND_WWW settings,
          append missing slashes and/or prepends missing "www."s.

            - If APPEND_SLASH is set and the initial URL doesn't end with a
              slash, and it is not found in urlpatterns, form a new URL by
              appending a slash at the end. If this new URL is found in
              urlpatterns, return an HTTP redirect to this new URL; otherwise
              process the initial URL as usual.

          This behavior can be customized by subclassing CommonMiddleware and
          overriding the response_redirect_class attribute.
    """

    response_redirect_class = HttpResponsePermanentRedirect

    def a(self, e):
        """
        Check for denied User-Agents and rewrite the URL based on
        settings.APPEND_SLASH and settings.PREPEND_WWW
        """

        # Check for denied User-Agents
        f = e.META.get("HTTP_USER_AGENT")
        if f is not None:
            for g in settings.DISALLOWED_USER_AGENTS:
                if g.search(f):
                    raise PermissionDenied("Forbidden user agent")

        # Check for a redirect based on settings.PREPEND_WWW
        h = e.get_host()

        if settings.PREPEND_WWW and h and not h.startswith("www."):
            # Check if we also need to append a slash so we can do it all
            # with a single redirect. (This check may be somewhat expensive,
            # so we only do it if we already know we're sending a redirect,
            # or in process_response if we get a 404.)
            if self.b(e):
                i = self.c(e)
            else:
                i = e.get_full_path()

            return self.response_redirect_class(f"{e.scheme}://www.{h}{i}")

    def b(self, j):
        """
        Return True if settings.APPEND_SLASH is True and appending a slash to
        the request path turns an invalid path into a valid one.
        """
        if settings.APPEND_SLASH and not j.path_info.endswith("/"):
            k = getattr(j, "urlconf", None)
            if not is_valid_path(j.path_info, k):
                l = is_valid_path("%s/" % j.path_info, k)
                if l:
                    m = l.func
                    return getattr(m, "should_append_slash", True)
        return False

    def c(self, n):
        """
        Return the full path of the request with a trailing slash appended.

        Raise a RuntimeError if settings.DEBUG is True and request.method is
        DELETE, POST, PUT, or PATCH.
        """
        o = n.get_full_path(force_append_slash=True)
        # Prevent construction of scheme relative urls.
        o = escape_leading_slashes(o)
        if settings.DEBUG and n.method in ("DELETE", "POST", "PUT", "PATCH"):
            raise RuntimeError(
                "You called this URL via %(method)s, but the URL doesn't end "
                "in a slash and you have APPEND_SLASH set. Django can't "
                "redirect to the slash URL while maintaining %(method)s data. "
                "Change your form to point to %(url)s (note the trailing "
                "slash), or set APPEND_SLASH=False in your Django settings."
                % {
                    "method": n.method,
                    "url": n.get_host() + o,
                }
            )
        return o

    def d(self, p, q):
        """
        When the status code of the response is 404, it may redirect to a path
        with an appended slash if should_redirect_with_slash() returns True.
        """
        # If the given URL is "Not Found", then check if we should redirect to
        # a path with a slash appended.
        if q.status_code == 404 and self.b(p):
            q = self.response_redirect_class(
                self.c(p)
            )

        # Add the Content-Length header to non-streaming responses if not
        # already set.
        if not q.streaming and not q.has_header("Content-Length"):
            q.headers["Content-Length"] = str(len(q.content))

        return q
