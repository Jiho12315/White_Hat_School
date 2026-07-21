from django.contrib import admin
from audit.services import record_audit
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "seller", "sale_status", "visibility_status", "created_at")
    list_filter = ("category", "sale_status", "visibility_status")
    search_fields = ("name", "description", "seller__username")
    readonly_fields = ("public_id",)

    def save_model(self, request, obj, form, change):
        old = Product.objects.get(pk=obj.pk).visibility_status if change else None
        super().save_model(request, obj, form, change)
        if old != obj.visibility_status:
            record_audit(actor=request.user, action="CHANGE_PRODUCT_VISIBILITY", target=obj, request=request, detail={"before": old, "after": obj.visibility_status})
