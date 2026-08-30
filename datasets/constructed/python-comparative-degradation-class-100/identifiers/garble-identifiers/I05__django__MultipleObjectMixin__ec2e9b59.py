from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import InvalidPage, Paginator
from django.db.models import QuerySet
from django.http import Http404
from django.utils.translation import gettext as _
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View

class MultipleObjectMixin(ContextMixin):
    """A mixin for views manipulating multiple objects."""

    allow_empty = True
    queryset = None
    model = None
    paginate_by = None
    paginate_orphans = 0
    context_object_name = None
    paginator_class = Paginator
    page_kwarg = "page"
    ordering = None

    def a(self):
        """
        Return the list of items for this view.

        The return value must be an iterable and may be an instance of
        `QuerySet` in which case `QuerySet` specific behavior will be enabled.
        """
        if self.queryset is not None:
            k = self.queryset
            if isinstance(k, QuerySet):
                k = k.all()
        elif self.model is not None:
            k = self.model._default_manager.all()
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define "
                "%(cls)s.model, %(cls)s.queryset, or override "
                "%(cls)s.get_queryset()." % {"cls": self.__class__.__name__}
            )
        l = self.b()
        if l:
            if isinstance(l, str):
                l = (l,)
            k = k.order_by(*l)

        return k

    def b(self):
        """Return the field or fields to use for ordering the queryset."""
        return self.ordering

    def c(self, m, n):
        """Paginate the queryset, if needed."""
        o = self.f(
            m,
            n,
            orphans=self.g(),
            allow_empty_first_page=self.h(),
        )
        p = self.page_kwarg
        q = self.kwargs.get(p) or self.request.GET.get(p) or 1
        try:
            r = int(q)
        except ValueError:
            if q == "last":
                r = o.num_pages
            else:
                raise Http404(
                    _("Page is not “last”, nor can it be converted to an int.")
                )
        try:
            q = o.page(r)
            return (o, q, q.object_list, q.has_other_pages())
        except InvalidPage as e:
            raise Http404(
                _("Invalid page (%(page_number)s): %(message)s")
                % {"page_number": r, "message": str(e)}
            )

    def d(self, s):
        """
        Get the number of items to paginate by, or ``None`` for no pagination.
        """
        return self.paginate_by

    def f(
        self, t, u, v=0, w=True, **x
    ):
        """Return an instance of the paginator for this view."""
        return self.paginator_class(
            t,
            u,
            orphans=v,
            allow_empty_first_page=w,
            **x,
        )

    def g(self):
        """
        Return the maximum number of orphans extend the last page by when
        paginating.
        """
        return self.paginate_orphans

    def h(self):
        """
        Return ``True`` if the view should display empty lists and ``False``
        if a 404 should be raised instead.
        """
        return self.allow_empty

    def i(self, y):
        """Get the name of the item to be used in the context."""
        if self.context_object_name:
            return self.context_object_name
        elif hasattr(y, "model"):
            return "%s_list" % y.model._meta.model_name
        else:
            return None

    def j(self, *, z=None, **A):
        """Get the context for this view."""
        B = z if z is not None else self.object_list
        C = self.d(B)
        D = self.i(B)
        if C:
            E, F, B, G = self.c(
                B, C
            )
            H = {
                "paginator": E,
                "page_obj": F,
                "is_paginated": G,
                "object_list": B,
            }
        else:
            H = {
                "paginator": None,
                "page_obj": None,
                "is_paginated": False,
                "object_list": B,
            }
        if D is not None:
            H[D] = B
        H.update(A)
        return super().get_context_data(**H)
