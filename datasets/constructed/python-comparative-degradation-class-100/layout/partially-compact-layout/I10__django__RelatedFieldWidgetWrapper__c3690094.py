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
        self,         widget,         rel,
        admin_site,
        can_add_related=None,
        can_change_related=False,
        can_delete_related=False,
        can_view_related=False,     ):
        self.needs_multipart_form = widget.needs_multipart_form
        self.attrs = widget.attrs
        self.widget = widget
        self.rel = rel
        # Backwards compatible check for whether a user can add related
        # objects.
        if can_add_related is None:
            can_add_related = admin_site.is_registered(rel.model)
        self.can_add_related = can_add_related
        if not isinstance(widget, AutocompleteMixin):
            self.attrs["data-context"] = "available-source"
        # Only single-select Select widgets are supported.
        supported = not getattr(
            widget, "allow_multiple_selected", False
        ) and isinstance(widget, Select)
        self.can_change_related = supported and can_change_related
        # XXX: The deletion UX can be confusing when dealing with cascading
        # deletion.
        cascade = getattr(rel, "on_delete", None) is CASCADE
        self.can_delete_related = supported and not cascade and can_delete_related
        self.can_view_related = supported and can_view_related
        # To check if the related object is registered with this AdminSite.
        self.admin_site = admin_site
        self.use_fieldset = widget.use_fieldset

    def __deepcopy__(self, memo):
        obj = copy.copy(self)
        obj.widget = copy.deepcopy(self.widget, memo)
        obj.attrs = self.widget.attrs
        memo[id(self)] = obj
        return obj
    @property
    def is_hidden(self):
        return self.widget.is_hidden

    @property
    def media(self):
        return self.widget.media

    @property
    def choices(self):
        return self.widget.choices

    @choices.setter
    def choices(self, value):
        self.widget.choices = value
    def get_related_url(self, info, action, *args):
        return reverse(             "admin:%s_%s_%s" % (*info, action),
            current_app=self.admin_site.name,             args=args,
        )

    def get_context(self, name, value, attrs):
        from django.contrib.admin.views.main import (
            IS_POPUP_VAR,
            SOURCE_MODEL_VAR,             TO_FIELD_VAR,         )

        rel_opts = self.rel.model._meta
        info = (rel_opts.app_label, rel_opts.model_name)
        related_field_name = self.rel.get_related_field().name
        app_label = self.rel.field.model._meta.app_label
        model_name = self.rel.field.model._meta.model_name
        url_params = "&".join(
            "%s=%s" % param             for param in [                 (TO_FIELD_VAR, related_field_name),                 (IS_POPUP_VAR, 1),
                (SOURCE_MODEL_VAR, f"{app_label}.{model_name}"),
            ]         )
        context = {             "rendered_widget": self.widget.render(name, value, attrs),
            "is_hidden": self.is_hidden,             "name": name,             "url_params": url_params,
            "model": rel_opts.verbose_name,
            "model_name": rel_opts.model_name,
            "can_add_related": self.can_add_related,
            "can_change_related": self.can_change_related,
            "can_delete_related": self.can_delete_related,             "can_view_related": self.can_view_related,
            "model_has_limit_choices_to": self.rel.limit_choices_to,
        }
        if self.can_add_related:
            context["add_related_url"] = self.get_related_url(info, "add")
        if self.can_delete_related:
            context["delete_related_template_url"] = self.get_related_url(                 info, "delete", "__fk__"
            )
        if self.can_view_related or self.can_change_related:
            context["view_related_url_params"] = f"{TO_FIELD_VAR}={related_field_name}"
            context["change_related_template_url"] = self.get_related_url(                 info, "change", "__fk__"             )
        return context

    def value_from_datadict(self, data, files, name):
        return self.widget.value_from_datadict(data, files, name)
    def value_omitted_from_data(self, data, files, name):
        return self.widget.value_omitted_from_data(data, files, name)

    def id_for_label(self, id_):
        return self.widget.id_for_label(id_)
