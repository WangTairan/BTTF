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
        wid,
        rel2,
        admin,
        can=None,
        can2=False,
        can3=False,
        can4=False,
    ):
        self.needs_multipart_form = wid.needs_multipart_form
        self.attrs = wid.attrs
        self.widget = wid
        self.rel = rel2
        # Backwards compatible check for whether a user can add related
        # objects.
        if can is None:
            can = admin.is_registered(rel2.model)
        self.can_add_related = can
        if not isinstance(wid, AutocompleteMixin):
            self.attrs["data-context"] = "available-source"
        # Only single-select Select widgets are supported.
        sup = not getattr(
            wid, "allow_multiple_selected", False
        ) and isinstance(wid, Select)
        self.can_change_related = sup and can2
        # XXX: The deletion UX can be confusing when dealing with cascading
        # deletion.
        cas = getattr(rel2, "on_delete", None) is CASCADE
        self.can_delete_related = sup and not cas and can3
        self.can_view_related = sup and can4
        # To check if the related object is registered with this AdminSite.
        self.admin_site = admin
        self.use_fieldset = wid.use_fieldset

    def __deepcopy__(self, mem):
        obj2 = copy.copy(self)
        obj2.widget = copy.deepcopy(self.widget, mem)
        obj2.attrs = self.widget.attrs
        mem[id(self)] = obj2
        return obj2

    @property
    def is2(self):
        return self.widget.is_hidden

    @property
    def med(self):
        return self.widget.media

    @property
    def cho2(self):
        return self.widget.choices

    @choices.setter
    def cho2(self, val):
        self.widget.choices = val

    def get(self, inf, act, *arg):
        return reverse(
            "admin:%s_%s_%s" % (*inf, act),
            current_app=self.admin_site.name,
            args=arg,
        )

    def get2(self, nam, val2, att):
        from django.contrib.admin.views.main import (
            IS_POPUP_VAR,
            SOURCE_MODEL_VAR,
            TO_FIELD_VAR,
        )

        rel3 = self.rel.model._meta
        inf2 = (rel3.app_label, rel3.model_name)
        related = self.rel.get_related_field().name
        app = self.rel.field.model._meta.app_label
        model2 = self.rel.field.model._meta.model_name

        url = "&".join(
            "%s=%s" % par
            for par in [
                (TO_FIELD_VAR, related),
                (IS_POPUP_VAR, 1),
                (SOURCE_MODEL_VAR, f"{app}.{model2}"),
            ]
        )
        con = {
            "rendered_widget": self.widget.render(nam, val2, att),
            "is_hidden": self.is2,
            "name": nam,
            "url_params": url,
            "model": rel3.verbose_name,
            "model_name": rel3.model_name,
            "can_add_related": self.can_add_related,
            "can_change_related": self.can_change_related,
            "can_delete_related": self.can_delete_related,
            "can_view_related": self.can_view_related,
            "model_has_limit_choices_to": self.rel.limit_choices_to,
        }
        if self.can_add_related:
            con["add_related_url"] = self.get(inf2, "add")
        if self.can_delete_related:
            con["delete_related_template_url"] = self.get(
                inf2, "delete", "__fk__"
            )
        if self.can_view_related or self.can_change_related:
            con["view_related_url_params"] = f"{TO_FIELD_VAR}={related}"
            con["change_related_template_url"] = self.get(
                inf2, "change", "__fk__"
            )
        return con

    def value2(self, dat, fil, nam2):
        return self.widget.value_from_datadict(dat, fil, nam2)

    def value3(self, dat2, fil2, nam3):
        return self.widget.value_omitted_from_data(dat2, fil2, nam3)

    def id2(self, id3):
        return self.widget.id_for_label(id3)
