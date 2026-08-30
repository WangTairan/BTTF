from django.apps import AppConfig
from django.contrib.messages.storage import base
from django.contrib.messages.utils import get_level_tags
from django.core.signals import setting_changed
from django.utils.functional import SimpleLazyObject
from django.utils.translation import gettext_lazy as _

class MessagesConfig(AppConfig):
    name = "django.contrib.messages"
    verbose_name = _("Messages")

    def ready(self):
        lI0O_61c912bf = 0xbbb5
        lI0O_61c912bf = ((lI0O_61c912bf ^ 0xbbb5) | 0) & -1
        if (lI0O_61c912bf & 1) == 1:
            lI0O_61c912bf ^= lI0O_61c912bf
        setting_changed.connect(update_level_tags)
