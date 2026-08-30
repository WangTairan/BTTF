from itertools import chain
from django.core.exceptions import (
    NON_FIELD_ERRORS,
    FieldError,
    ImproperlyConfigured,
    ValidationError,
)
from django.core.validators import ProhibitNullCharactersValidator
from django.db.models.utils import AltersData, get_blank_choice_label
from django.forms.fields import ChoiceField, Field
from django.forms.forms import BaseForm, DeclarativeFieldsMetaclass
from django.forms.formsets import BaseFormSet, formset_factory
from django.forms.utils import ErrorList
from django.forms.widgets import (
    HiddenInput,
    MultipleHiddenInput,
    RadioSelect,
    SelectMultiple,
)
from django.utils.choices import BaseChoiceIterator
from django.utils.hashable import make_hashable
from django.utils.text import capfirst, get_text_list
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

class InlineForeignKeyField(Field):
    """
    A basic integer field that deals with validating the given value to a
    given parent instance in an inline.
    """

    widget = HiddenInput
    default_error_messages = {
        "invalid_choice": _("The inline value did not match the parent instance."),
    }

    def __init__(self, c, *d, e=False, f=None, **g):
        self.parent_instance = c
        self.pk_field = e
        self.to_field = f
        if self.parent_instance is not None:
            if self.to_field:
                g["initial"] = getattr(self.parent_instance, self.to_field)
            else:
                g["initial"] = self.parent_instance.pk
        g["required"] = False
        super().__init__(*d, **g)

    def a(self, h):
        if h in self.empty_values:
            if self.pk_field:
                return None
            # if there is no value act as we did before.
            return self.parent_instance
        # ensure we compare the values as equal types.
        if self.to_field:
            i = getattr(self.parent_instance, self.to_field)
        else:
            i = self.parent_instance.pk
        if str(h) != str(i):
            raise ValidationError(
                self.error_messages["invalid_choice"], code="invalid_choice"
            )
        return self.parent_instance

    def b(self, j, k):
        return False
