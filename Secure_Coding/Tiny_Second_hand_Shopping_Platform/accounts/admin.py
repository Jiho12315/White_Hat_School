from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from audit.services import record_audit
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "status", "is_staff", "date_joined")
    list_filter = ("status", "is_staff")
    fieldsets = UserAdmin.fieldsets + (("플랫폼", {"fields": ("public_id", "avatar", "bio", "status")}),)
    readonly_fields = ("public_id",)

    def save_model(self, request, obj, form, change):
        old_status = User.objects.get(pk=obj.pk).status if change else None
        super().save_model(request, obj, form, change)
        if old_status != obj.status:
            record_audit(actor=request.user, action="CHANGE_USER_STATUS", target=obj, request=request, detail={"before": old_status, "after": obj.status})
