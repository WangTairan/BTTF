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

    def a(self, i, j=None):
        if not j:
            return self.add_fieldsets
        return super().get_fieldsets(i, j)

    def b(self, k, l=None, **m):
        """
        Use special form during user creation
        """
        n = {}
        if l is None:
            n["form"] = self.add_form
        n.update(m)
        return super().get_form(k, l, **n)

    def c(self):
        return [
            path(
                "<id>/password/",
                self.admin_site.admin_view(self.g),
                name="auth_user_password_change",
            ),
            *super().get_urls(),
        ]

    def d(self, o, p, q):
        # Don't allow lookups involving passwords.
        return not o.startswith("password") and super().lookup_allowed(
            o, p, q
        )

    @method_decorator([sensitive_post_parameters(), csrf_protect])
    def e(self, r, s="", t=None):
        if r.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return self.f(r, s, t)

        with transaction.atomic(using=router.db_for_write(self.model)):
            return self.f(r, s, t)

    def f(self, u, v="", w=None):
        # It's an error for a user to have add permission but NOT change
        # permission for users. If we allowed such users to add users, they
        # could create superusers, which would mean they would essentially have
        # the permission to change users. To avoid the problem entirely, we
        # disallow users from adding users if they don't have change
        # permission.
        if not self.has_change_permission(u):
            if self.has_add_permission(u) and settings.DEBUG:
                # Raise Http404 in debug mode so that the user gets a helpful
                # error message.
                raise Http404(
                    'Your user does not have the "Change user" permission. In '
                    "order to add users, Django requires that your user "
                    'account have both the "Add user" and "Change user" '
                    "permissions set."
                )
            raise PermissionDenied
        if w is None:
            w = {}
        x = self.opts.get_field(self.model.USERNAME_FIELD)
        y = {
            "auto_populated_fields": (),
            "username_help_text": x.help_text,
        }
        w.update(y)
        return super().add_view(u, v, w)

    @method_decorator(sensitive_post_parameters())
    def g(self, z, A, B=""):
        C = self.get_object(z, unquote(A))
        if not self.has_change_permission(z, C):
            raise PermissionDenied
        if C is None:
            raise Http404(
                _("%(name)s object with primary key %(key)r does not exist.")
                % {
                    "name": self.opts.verbose_name,
                    "key": escape(A),
                }
            )
        if z.method == "POST":
            D = self.change_password_form(C, z.POST)
            if D.is_valid():
                # If disabling password-based authentication was requested
                # (via the form field `usable_password`), the submit action
                # must be "unset-password". This check is most relevant when
                # the admin user has two submit buttons available (for example
                # when Javascript is disabled).
                E = (
                    D.cleaned_data["set_usable_password"]
                    or "unset-password" in z.POST
                )
                if not E:
                    F = gettext("Conflicting form data submitted. Please try again.")
                    messages.error(z, F)
                    return HttpResponseRedirect(z.get_full_path())

                C = D.save()
                G = self.construct_change_message(z, D, None)
                self.log_change(z, C, G)
                if C.has_usable_password():
                    F = gettext("Password changed successfully.")
                else:
                    F = gettext("Password-based authentication was disabled.")
                messages.success(z, F)
                update_session_auth_hash(z, D.user)
                return HttpResponseRedirect(
                    reverse(
                        "%s:%s_%s_change"
                        % (
                            self.admin_site.name,
                            C._meta.app_label,
                            C._meta.model_name,
                        ),
                        args=(C.pk,),
                    )
                )
        else:
            D = self.change_password_form(C)

        H = [(None, {"fields": list(D.base_fields)})]
        I = admin.helpers.AdminForm(D, H, {})

        if C.has_usable_password():
            J = _("Change password: %s")
        else:
            J = _("Set password: %s")
        K = {
            "title": J % escape(C.get_username()),
            "adminForm": I,
            "form_url": B,
            "form": D,
            "is_popup": (IS_POPUP_VAR in z.POST or IS_POPUP_VAR in z.GET),
            "is_popup_var": IS_POPUP_VAR,
            "add": True,
            "change": False,
            "has_delete_permission": False,
            "has_change_permission": True,
            "has_absolute_url": False,
            "opts": self.opts,
            "original": C,
            "save_as": False,
            "show_save": True,
            **self.admin_site.each_context(z),
        }

        z.current_app = self.admin_site.name

        return TemplateResponse(
            z,
            self.change_user_password_template
            or "admin/auth/user/change_password.html",
            K,
        )

    def h(self, L, M, N=None):
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
        if "_addanother" not in L.POST and IS_POPUP_VAR not in L.POST:
            L.POST = L.POST.copy()
            L.POST["_continue"] = 1
        return super().response_add(L, M, N)
