import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from products.models import Product


class Report(models.Model):
    class ReasonCategory(models.TextChoices):
        FRAUD = "FRAUD", "사기 또는 허위 판매"
        PROHIBITED = "PROHIBITED", "판매 금지 품목"
        COUNTERFEIT = "COUNTERFEIT", "위조품 또는 모조품"
        INAPPROPRIATE = "INAPPROPRIATE", "부적절한 상품 정보"
        SPAM = "SPAM", "도배 또는 광고"
        OTHER = "OTHER", "기타"

    class Status(models.TextChoices):
        PENDING = "PENDING", "대기"
        APPROVED = "APPROVED", "승인"
        REJECTED = "REJECTED", "기각"
        ON_HOLD = "ON_HOLD", "보류"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="submitted_reports")
    reported_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="received_reports")
    reported_product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True, related_name="reports")
    reason_category = models.CharField(max_length=20, choices=ReasonCategory.choices, default=ReasonCategory.OTHER)
    reason = models.CharField(max_length=1000)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="reviewed_reports")
    review_note = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(Q(reported_user__isnull=False, reported_product__isnull=True) | Q(reported_user__isnull=True, reported_product__isnull=False)),
                name="report_exactly_one_target",
            ),
            models.UniqueConstraint(fields=["reporter", "reported_user"], condition=Q(reported_user__isnull=False), name="unique_user_report"),
            models.UniqueConstraint(fields=["reporter", "reported_product"], condition=Q(reported_product__isnull=False), name="unique_product_report"),
        ]

    def clean(self):
        if bool(self.reported_user) == bool(self.reported_product):
            raise ValidationError("신고 대상은 사용자 또는 상품 중 하나여야 합니다.")
        if self.reported_user_id and self.reporter_id == self.reported_user_id:
            raise ValidationError("자기 자신을 신고할 수 없습니다.")
        if self.reported_product_id and self.reported_product.seller_id == self.reporter_id:
            raise ValidationError("자신의 상품을 신고할 수 없습니다.")
