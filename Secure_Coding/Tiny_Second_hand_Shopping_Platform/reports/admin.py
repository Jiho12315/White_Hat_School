from django.contrib import admin
from django.utils import timezone
from audit.services import record_audit
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("public_id", "reporter", "reason_category", "status", "created_at", "reviewer")
    list_filter = ("reason_category", "status", "created_at")
    readonly_fields = ("public_id", "reporter", "reported_user", "reported_product", "reason_category", "reason", "created_at")

    def save_model(self, request, obj, form, change):
        old = Report.objects.get(pk=obj.pk).status if change else None
        obj.reviewer = request.user
        obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
        record_audit(actor=request.user, action="REVIEW_REPORT", target=obj, request=request, detail={"before": old, "after": obj.status})
