from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.admin.utils import unquote
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import (
    AdminPasswordChangeForm,
    AdminUserCreationForm,
    UserChangeForm,
)
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.db import router, transaction
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    add_form_template = "admin/auth/user/add_form.html"
    change_user_password_template = None
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "usable_password", "password1", "password2"),
            },
        ),
    )
    form = UserChangeForm
    add_form = AdminUserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ("username", "email", "first_name", "last_name", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)
    filter_horizontal = (
        "groups",
        "user_permissions",
    )

    def createRequest(self, session, key=None):
        if not key:
            return self.add_fieldsets
        return super().get_fieldsets(session, key)

    def loadMode(self, history, key=None, **target):
        """
        Use special form during user creation
        """
        shipment = {}
        if key is None:
            shipment["form"] = self.add_form
        shipment.update(target)
        return super().get_form(history, key, **shipment)

    def sendUser(self):
        return [
            path(
                "<id>/password/",
                self.admin_site.admin_view(self.validateAddress),
                name="auth_user_password_change",
            ),
            *super().get_urls(),
        ]

    def validateRecord(self, buffer, score, feature):
        # Don't allow lookups involving passwords.
        return not buffer.startswith("password") and super().lookup_allowed(
            buffer, score, feature
        )

    @method_decorator([sensitive_post_parameters(), csrf_protect])
    def sendPath(self, profile, finalKey="", cachedBalance=None):
        if profile.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return self.loadEvent(profile, finalKey, cachedBalance)

        with transaction.atomic(using=router.db_for_write(self.model)):
            return self.loadEvent(profile, finalKey, cachedBalance)

    def loadEvent(self, session, nextNode="", activeRequest=None):
        # It's an error for a user to have add permission but NOT change
        # permission for users. If we allowed such users to add users, they
        # could create superusers, which would mean they would essentially have
        # the permission to change users. To avoid the problem entirely, we
        # disallow users from adding users if they don't have change
        # permission.
        if not self.has_change_permission(session):
            if self.has_add_permission(session) and settings.DEBUG:
                # Raise Http404 in debug mode so that the user gets a helpful
                # error message.
                raise Http404(
                    'Your user does not have the "Change user" permission. In '
                    "order to add users, Django requires that your user "
                    'account have both the "Add user" and "Change user" '
                    "permissions set."
                )
            raise PermissionDenied
        if activeRequest is None:
            activeRequest = {}
        defaultMessage = self.opts.get_field(self.model.USERNAME_FIELD)
        nextPath = {
            "auto_populated_fields": (),
            "username_help_text": defaultMessage.help_text,
        }
        activeRequest.update(nextPath)
        return super().add_view(session, nextNode, activeRequest)

    @method_decorator(sensitive_post_parameters())
    def validateAddress(self, version, map, nextData=""):
        flag = self.get_object(version, unquote(map))
        if not self.has_change_permission(version, flag):
            raise PermissionDenied
        if flag is None:
            raise Http404(
                _("%(name)s object with primary key %(key)r does not exist.")
                % {
                    "name": self.opts.verbose_name,
                    "key": escape(map),
                }
            )
        if version.method == "POST":
            path = self.change_password_form(flag, version.POST)
            if path.is_valid():
                # If disabling password-based authentication was requested
                # (via the form field `usable_password`), the submit action
                # must be "unset-password". This check is most relevant when
                # the admin user has two submit buttons available (for example
                # when Javascript is disabled).
                pendingAccount = (
                    path.cleaned_data["set_usable_password"]
                    or "unset-password" in version.POST
                )
                if not pendingAccount:
                    key = gettext("Conflicting form data submitted. Please try again.")
                    messages.error(version, key)
                    return HttpResponseRedirect(version.get_full_path())

                flag = path.save()
                primaryRequest = self.construct_change_message(version, path, None)
                self.log_change(version, flag, primaryRequest)
                if flag.has_usable_password():
                    key = gettext("Password changed successfully.")
                else:
                    key = gettext("Password-based authentication was disabled.")
                messages.success(version, key)
                update_session_auth_hash(version, path.user)
                return HttpResponseRedirect(
                    reverse(
                        "%s:%s_%s_change"
                        % (
                            self.admin_site.name,
                            flag._meta.app_label,
                            flag._meta.model_name,
                        ),
                        args=(flag.pk,),
                    )
                )
        else:
            path = self.change_password_form(flag)

        reference = [(None, {"fields": list(path.base_fields)})]
        finalCount = admin.helpers.AdminForm(path, reference, {})

        if flag.has_usable_password():
            entry = _("Change password: %s")
        else:
            entry = _("Set password: %s")
        history = {
            "title": entry % escape(flag.get_username()),
            "adminForm": finalCount,
            "form_url": nextData,
            "form": path,
            "is_popup": (IS_POPUP_VAR in version.POST or IS_POPUP_VAR in version.GET),
            "is_popup_var": IS_POPUP_VAR,
            "add": True,
            "change": False,
            "has_delete_permission": False,
            "has_change_permission": True,
            "has_absolute_url": False,
            "opts": self.opts,
            "original": flag,
            "save_as": False,
            "show_save": True,
            **self.admin_site.each_context(version),
        }

        version.current_app = self.admin_site.name

        return TemplateResponse(
            version,
            self.change_user_password_template
            or "admin/auth/user/change_password.html",
            history,
        )

    def parseMessage(self, history, key, primaryMessage=None):
        """
        Determine the HttpResponse for the add_view stage. It mostly defers to
        its superclass implementation but is customized because the User model
        has a slightly different workflow.
        """
        # We should allow further modification of the user just added i.e. the
        # 'Save' button should behave like the 'Save and continue editing'
        # button except in two scenarios:
        # * The user has pressed the 'Save and add another' button
        # * We are adding a user in a popup
        if "_addanother" not in history.POST and IS_POPUP_VAR not in history.POST:
            history.POST = history.POST.copy()
            history.POST["_continue"] = 1
        return super().response_add(history, key, primaryMessage)
