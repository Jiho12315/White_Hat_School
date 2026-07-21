from django.conf import settings
from django.db import transaction

from accounts.models import User
from audit.services import record_audit
from products.models import Product
from .models import Report


@transaction.atomic
def apply_report_threshold(report, request=None):
    if report.reported_product_id:
        count = Report.objects.filter(reported_product=report.reported_product).exclude(status=Report.Status.REJECTED).count()
        if count >= settings.PRODUCT_REPORT_THRESHOLD:
            product = Product.objects.select_for_update().get(pk=report.reported_product_id)
            if product.visibility_status == Product.Visibility.PUBLIC:
                product.visibility_status = Product.Visibility.UNDER_REVIEW
                product.save(update_fields=["visibility_status", "updated_at"])
                record_audit(actor=None, action="AUTO_RESTRICT_PRODUCT", target=product, request=request, detail={"report_count": count})
    else:
        count = Report.objects.filter(reported_user=report.reported_user).exclude(status=Report.Status.REJECTED).count()
        if count >= settings.USER_REPORT_THRESHOLD:
            user = User.objects.select_for_update().get(pk=report.reported_user_id)
            if user.status == User.Status.ACTIVE:
                user.status = User.Status.RESTRICTED
                user.save(update_fields=["status"])
                record_audit(actor=None, action="AUTO_RESTRICT_USER", target=user, request=request, detail={"report_count": count})
