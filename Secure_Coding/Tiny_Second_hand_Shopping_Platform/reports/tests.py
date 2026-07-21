from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from products.models import Product
from .models import Report


class ProductReportFlowTests(TestCase):
    def setUp(self):
        self.password = "Strong-test-pass-2026"
        self.seller = User.objects.create_user(username="seller", password=self.password)
        self.reporter = User.objects.create_user(username="reporter", password=self.password)
        self.other_seller = User.objects.create_user(username="other", password=self.password)
        self.product = Product.objects.create(
            seller=self.seller,
            name="신고 대상 노트북",
            description="상품 설명",
            price=100000,
        )
        self.client.force_login(self.reporter)

    def test_product_report_page_shows_fixed_product_name(self):
        response = self.client.get(reverse("reports:product_create", args=[self.product.public_id]))
        self.assertContains(response, self.product.name)
        self.assertNotContains(response, 'name="target_id"')
        self.assertNotContains(response, 'name="target_type"')
        self.assertContains(response, 'name="reason_category"')
        self.assertContains(response, 'name="reason"')

    def test_product_report_target_cannot_be_changed_in_post_data(self):
        other_product = Product.objects.create(
            seller=self.other_seller,
            name="다른 상품",
            description="다른 설명",
            price=200000,
        )
        response = self.client.post(
            reverse("reports:product_create", args=[self.product.public_id]),
            {
                "target_type": "product",
                "target_id": str(other_product.public_id),
                "reason_category": Report.ReasonCategory.FRAUD,
                "reason": "상품 설명과 실제 안내가 다릅니다.",
            },
        )
        self.assertRedirects(response, reverse("core:home"))
        report = Report.objects.get(reporter=self.reporter)
        self.assertEqual(report.reported_product, self.product)
        self.assertEqual(report.reason_category, Report.ReasonCategory.FRAUD)

    def test_reported_product_detail_shows_completed_instead_of_report_link(self):
        Report.objects.create(
            reporter=self.reporter,
            reported_product=self.product,
            reason_category=Report.ReasonCategory.COUNTERFEIT,
            reason="위조품으로 의심됩니다.",
        )
        response = self.client.get(reverse("products:detail", args=[self.product.public_id]))
        self.assertContains(response, "신고 완료")
        self.assertNotContains(response, reverse("reports:product_create", args=[self.product.public_id]))

    def test_my_page_shows_only_current_users_submitted_reports(self):
        Report.objects.create(
            reporter=self.reporter,
            reported_product=self.product,
            reason_category=Report.ReasonCategory.INAPPROPRIATE,
            reason="현재 사용자 신고 상세 내용",
        )
        other_product = Product.objects.create(
            seller=self.other_seller,
            name="다른 사용자의 신고 대상",
            description="다른 설명",
            price=300000,
        )
        Report.objects.create(
            reporter=self.seller,
            reported_product=other_product,
            reason="표시되면 안 되는 신고",
        )
        response = self.client.get(reverse("accounts:me"), {"section": "reports"})
        self.assertContains(response, self.product.name)
        self.assertContains(response, "현재 사용자 신고 상세 내용")
        self.assertNotContains(response, "표시되면 안 되는 신고")
        self.assertContains(response, 'data-active-section="reports"')

# Create your tests here.
