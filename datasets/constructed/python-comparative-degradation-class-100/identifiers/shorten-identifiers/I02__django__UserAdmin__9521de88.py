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

    def get(self, req, obj2=None):
        if not obj2:
            return self.add_fieldsets
        return super().get_fieldsets(req, obj2)

    def get2(self, req2, obj3=None, **kwa):
        """
        Use special form during user creation
        """
        def2 = {}
        if obj3 is None:
            def2["form"] = self.add_form
        def2.update(kwa)
        return super().get_form(req2, obj3, **def2)

    def get3(self):
        return [
            path(
                "<id>/password/",
                self.admin_site.admin_view(self.user2),
                name="auth_user_password_change",
            ),
            *super().get_urls(),
        ]

    def lookup2(self, loo, val, req3):
        # Don't allow lookups involving passwords.
        return not loo.startswith("password") and super().lookup_allowed(
            loo, val, req3
        )

    @method_decorator([sensitive_post_parameters(), csrf_protect])
    def add(self, req4, form2="", extra=None):
        if req4.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return self.add2(req4, form2, extra)

        with transaction.atomic(using=router.db_for_write(self.model)):
            return self.add2(req4, form2, extra)

    def add2(self, req5, form3="", extra2=None):
        # It's an error for a user to have add permission but NOT change
        # permission for users. If we allowed such users to add users, they
        # could create superusers, which would mean they would essentially have
        # the permission to change users. To avoid the problem entirely, we
        # disallow users from adding users if they don't have change
        # permission.
        if not self.has_change_permission(req5):
            if self.has_add_permission(req5) and settings.DEBUG:
                # Raise Http404 in debug mode so that the user gets a helpful
                # error message.
                raise Http404(
                    'Your user does not have the "Change user" permission. In '
                    "order to add users, Django requires that your user "
                    'account have both the "Add user" and "Change user" '
                    "permissions set."
                )
            raise PermissionDenied
        if extra2 is None:
            extra2 = {}
        username = self.opts.get_field(self.model.USERNAME_FIELD)
        def3 = {
            "auto_populated_fields": (),
            "username_help_text": username.help_text,
        }
        extra2.update(def3)
        return super().add_view(req5, form3, extra2)

    @method_decorator(sensitive_post_parameters())
    def user2(self, req6, id2, form4=""):
        use = self.get_object(req6, unquote(id2))
        if not self.has_change_permission(req6, use):
            raise PermissionDenied
        if use is None:
            raise Http404(
                _("%(name)s object with primary key %(key)r does not exist.")
                % {
                    "name": self.opts.verbose_name,
                    "key": escape(id2),
                }
            )
        if req6.method == "POST":
            for2 = self.change_password_form(use, req6.POST)
            if for2.is_valid():
                # If disabling password-based authentication was requested
                # (via the form field `usable_password`), the submit action
                # must be "unset-password". This check is most relevant when
                # the admin user has two submit buttons available (for example
                # when Javascript is disabled).
                valid = (
                    for2.cleaned_data["set_usable_password"]
                    or "unset-password" in req6.POST
                )
                if not valid:
                    msg2 = gettext("Conflicting form data submitted. Please try again.")
                    messages.error(req6, msg2)
                    return HttpResponseRedirect(req6.get_full_path())

                use = for2.save()
                change = self.construct_change_message(req6, for2, None)
                self.log_change(req6, use, change)
                if use.has_usable_password():
                    msg2 = gettext("Password changed successfully.")
                else:
                    msg2 = gettext("Password-based authentication was disabled.")
                messages.success(req6, msg2)
                update_session_auth_hash(req6, for2.user)
                return HttpResponseRedirect(
                    reverse(
                        "%s:%s_%s_change"
                        % (
                            self.admin_site.name,
                            use._meta.app_label,
                            use._meta.model_name,
                        ),
                        args=(use.pk,),
                    )
                )
        else:
            for2 = self.change_password_form(use)

        fie = [(None, {"fields": list(for2.base_fields)})]
        admin2 = admin.helpers.AdminForm(for2, fie, {})

        if use.has_usable_password():
            tit = _("Change password: %s")
        else:
            tit = _("Set password: %s")
        con = {
            "title": tit % escape(use.get_username()),
            "adminForm": admin2,
            "form_url": form4,
            "form": for2,
            "is_popup": (IS_POPUP_VAR in req6.POST or IS_POPUP_VAR in req6.GET),
            "is_popup_var": IS_POPUP_VAR,
            "add": True,
            "change": False,
            "has_delete_permission": False,
            "has_change_permission": True,
            "has_absolute_url": False,
            "opts": self.opts,
            "original": use,
            "save_as": False,
            "show_save": True,
            **self.admin_site.each_context(req6),
        }

        req6.current_app = self.admin_site.name

        return TemplateResponse(
            req6,
            self.change_user_password_template
            or "admin/auth/user/change_password.html",
            con,
        )

    def response(self, req7, obj4, post=None):
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
        if "_addanother" not in req7.POST and IS_POPUP_VAR not in req7.POST:
            req7.POST = req7.POST.copy()
            req7.POST["_continue"] = 1
        return super().response_add(req7, obj4, post)
