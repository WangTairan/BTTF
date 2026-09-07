import copy
import json
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db.models import CASCADE, UUIDField
from django.forms.widgets import Select
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.html import smart_urlquote
from django.utils.http import urlencode
from django.utils.text import Truncator
from django.utils.translation import get_language
from django.utils.translation import gettext as _

class RelatedFieldWidgetWrapper(forms.Widget):
    """
    This class is a wrapper to a given widget to add the add icon for the
    admin interface.
    """

    template_name = "admin/widgets/related_widget_wrapper.html"

    def __init__(
        self,
        j,
        k,
        l,
        m=None,
        n=False,
        o=False,
        p=False,
    ):
        self.needs_multipart_form = j.needs_multipart_form
        self.attrs = j.attrs
        self.widget = j
        self.rel = k
        # Backwards compatible check for whether a user can add related
        # objects.
        if m is None:
            m = l.is_registered(k.model)
        self.can_add_related = m
        if not isinstance(j, AutocompleteMixin):
            self.attrs["data-context"] = "available-source"
        # Only single-select Select widgets are supported.
        q = not getattr(
            j, "allow_multiple_selected", False
        ) and isinstance(j, Select)
        self.can_change_related = q and n
        # XXX: The deletion UX can be confusing when dealing with cascading
        # deletion.
        r = getattr(k, "on_delete", None) is CASCADE
        self.can_delete_related = q and not r and o
        self.can_view_related = q and p
        # To check if the related object is registered with this AdminSite.
        self.admin_site = l
        self.use_fieldset = j.use_fieldset

    def __deepcopy__(self, s):
        t = copy.copy(self)
        t.widget = copy.deepcopy(self.widget, s)
        t.attrs = self.widget.attrs
        s[id(self)] = t
        return t

    @property
    def a(self):
        return self.widget.is_hidden

    @property
    def b(self):
        return self.widget.media

    @property
    def d(self):
        return self.widget.choices

    @choices.setter
    def d(self, u):
        self.widget.choices = u

    def e(self, v, w, *x):
        return reverse(
            "admin:%s_%s_%s" % (*v, w),
            current_app=self.admin_site.name,
            args=x,
        )

    def f(self, y, z, A):
        from django.contrib.admin.views.main import (
            IS_POPUP_VAR,
            SOURCE_MODEL_VAR,
            TO_FIELD_VAR,
        )

        B = self.rel.model._meta
        C = (B.app_label, B.model_name)
        D = self.rel.get_related_field().name
        E = self.rel.field.model._meta.app_label
        F = self.rel.field.model._meta.model_name

        G = "&".join(
            "%s=%s" % H
            for H in [
                (TO_FIELD_VAR, D),
                (IS_POPUP_VAR, 1),
                (SOURCE_MODEL_VAR, f"{E}.{F}"),
            ]
        )
        I = {
            "rendered_widget": self.widget.render(y, z, A),
            "is_hidden": self.a,
            "name": y,
            "url_params": G,
            "model": B.verbose_name,
            "model_name": B.model_name,
            "can_add_related": self.can_add_related,
            "can_change_related": self.can_change_related,
            "can_delete_related": self.can_delete_related,
            "can_view_related": self.can_view_related,
            "model_has_limit_choices_to": self.rel.limit_choices_to,
        }
        if self.can_add_related:
            I["add_related_url"] = self.e(C, "add")
        if self.can_delete_related:
            I["delete_related_template_url"] = self.e(
                C, "delete", "__fk__"
            )
        if self.can_view_related or self.can_change_related:
            I["view_related_url_params"] = f"{TO_FIELD_VAR}={D}"
            I["change_related_template_url"] = self.e(
                C, "change", "__fk__"
            )
        return I

    def g(self, J, K, L):
        return self.widget.value_from_datadict(J, K, L)

    def h(self, M, N, O):
        return self.widget.value_omitted_from_data(M, N, O)

    def i(self, P):
        return self.widget.id_for_label(P)
