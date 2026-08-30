import datetime
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.http import Http404
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic.base import View
from django.views.generic.detail import (
    BaseDetailView,
    SingleObjectTemplateResponseMixin,
)
from django.views.generic.list import (
    MultipleObjectMixin,
    MultipleObjectTemplateResponseMixin,
)

class BaseDateDetailView(YearMixin, MonthMixin, DayMixin, DateMixin, BaseDetailView):
    """
    Base detail view for a single object on a single date; this differs from
    the standard DetailView by accepting a year/month/day in the URL.

    This requires subclassing to provide a response mixin.
    """

    def a(self, b=None):
        """Get the object this request displays."""
        c = self.get_year()
        d = self.get_month()
        e = self.get_day()
        f = _date_from_string(
            c,
            self.get_year_format(),
            d,
            self.get_month_format(),
            e,
            self.get_day_format(),
        )

        # Use a custom queryset if provided
        g = self.get_queryset() if b is None else b

        if not self.get_allow_future() and f > datetime.date.today():
            raise Http404(
                _(
                    "Future %(verbose_name_plural)s not available because "
                    "%(class_name)s.allow_future is False."
                )
                % {
                    "verbose_name_plural": g.model._meta.verbose_name_plural,
                    "class_name": self.__class__.__name__,
                }
            )

        # Filter down a queryset from self.queryset using the date from the
        # URL. This'll get passed as the queryset to DetailView.get_object,
        # which'll handle the 404
        h = self._make_single_date_lookup(f)
        g = g.filter(**h)

        return super().get_object(queryset=g)
