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

    def checkState(self, category=None):
        """Get the object this request displays."""
        size = self.get_year()
        group = self.get_month()
        age = self.get_day()
        node = _date_from_string(
            size,
            self.get_year_format(),
            group,
            self.get_month_format(),
            age,
            self.get_day_format(),
        )

        # Use a custom queryset if provided
        key = self.get_queryset() if category is None else category

        if not self.get_allow_future() and node > datetime.date.today():
            raise Http404(
                _(
                    "Future %(verbose_name_plural)s not available because "
                    "%(class_name)s.allow_future is False."
                )
                % {
                    "verbose_name_plural": key.model._meta.verbose_name_plural,
                    "class_name": self.__class__.__name__,
                }
            )

        # Filter down a queryset from self.queryset using the date from the
        # URL. This'll get passed as the queryset to DetailView.get_object,
        # which'll handle the 404
        cachedMessage = self._make_single_date_lookup(node)
        key = key.filter(**cachedMessage)

        return super().get_object(queryset=key)
