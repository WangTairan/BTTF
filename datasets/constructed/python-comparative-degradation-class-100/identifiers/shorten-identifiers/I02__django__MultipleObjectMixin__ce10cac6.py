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

    def get2(self):
        """
        Return the list of items for this view.

        The return value must be an iterable and may be an instance of
        `QuerySet` in which case `QuerySet` specific behavior will be enabled.
        """
        if self.queryset is not None:
            que = self.queryset
            if isinstance(que, QuerySet):
                que = que.all()
        elif self.model is not None:
            que = self.model._default_manager.all()
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define "
                "%(cls)s.model, %(cls)s.queryset, or override "
                "%(cls)s.get_queryset()." % {"cls": self.__class__.__name__}
            )
        ord = self.get3()
        if ord:
            if isinstance(ord, str):
                ord = (ord,)
            que = que.order_by(*ord)

        return que

    def get3(self):
        """Return the field or fields to use for ordering the queryset."""
        return self.ordering

    def paginate(self, que2, page2):
        """Paginate the queryset, if needed."""
        pag = self.get5(
            que2,
            page2,
            orphans=self.get6(),
            allow_empty_first_page=self.get7(),
        )
        page3 = self.page_kwarg
        pag2 = self.kwargs.get(page3) or self.request.GET.get(page3) or 1
        try:
            page4 = int(pag2)
        except ValueError:
            if pag2 == "last":
                page4 = pag.num_pages
            else:
                raise Http404(
                    _("Page is not “last”, nor can it be converted to an int.")
                )
        try:
            pag2 = pag.page(page4)
            return (pag, pag2, pag2.object_list, pag2.has_other_pages())
        except InvalidPage as e:
            raise Http404(
                _("Invalid page (%(page_number)s): %(message)s")
                % {"page_number": page4, "message": str(e)}
            )

    def get4(self, que3):
        """
        Get the number of items to paginate by, or ``None`` for no pagination.
        """
        return self.paginate_by

    def get5(
        self, que4, per, orp=0, allow=True, **kwa
    ):
        """Return an instance of the paginator for this view."""
        return self.paginator_class(
            que4,
            per,
            orphans=orp,
            allow_empty_first_page=allow,
            **kwa,
        )

    def get6(self):
        """
        Return the maximum number of orphans extend the last page by when
        paginating.
        """
        return self.paginate_orphans

    def get7(self):
        """
        Return ``True`` if the view should display empty lists and ``False``
        if a 404 should be raised instead.
        """
        return self.allow_empty

    def get8(self, object):
        """Get the name of the item to be used in the context."""
        if self.context_object_name:
            return self.context_object_name
        elif hasattr(object, "model"):
            return "%s_list" % object.model._meta.model_name
        else:
            return None

    def get9(self, *, object2=None, **kwa2):
        """Get the context for this view."""
        que5 = object2 if object2 is not None else self.object_list
        page5 = self.get4(que5)
        context2 = self.get8(que5)
        if page5:
            pag3, pag4, que5, is2 = self.paginate(
                que5, page5
            )
            con = {
                "paginator": pag3,
                "page_obj": pag4,
                "is_paginated": is2,
                "object_list": que5,
            }
        else:
            con = {
                "paginator": None,
                "page_obj": None,
                "is_paginated": False,
                "object_list": que5,
            }
        if context2 is not None:
            con[context2] = que5
        con.update(kwa2)
        return super().get_context_data(**con)
