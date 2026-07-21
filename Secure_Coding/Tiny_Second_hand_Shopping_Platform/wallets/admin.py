from django.contrib import admin
from .models import PointTransaction, Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "updated_at")
    readonly_fields = ("user", "balance", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PointTransaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("public_id", "sender", "receiver", "amount", "created_at")
    search_fields = ("sender__username", "receiver__username")
    readonly_fields = tuple(field.name for field in PointTransaction._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
