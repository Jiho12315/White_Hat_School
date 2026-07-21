import uuid

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from audit.models import AuditLog
from chat.models import ChatParticipant, ChatRoom, Message
from products.models import Product
from reports.models import Report
from reports.services import apply_report_threshold
from wallets.models import PointTransaction
from wallets.services import transfer_points


class PlatformTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.password = "Strong-test-pass-2026"
        self.alice = User.objects.create_user(username="alice", password=self.password)
        self.bob = User.objects.create_user(username="bob", password=self.password)

    def test_new_user_gets_configured_wallet(self):
        self.assertEqual(self.alice.wallet.balance, settings.INITIAL_POINT_BALANCE)

    def test_plain_password_is_not_stored(self):
        self.assertNotEqual(self.alice.password, self.password)
        self.assertTrue(self.alice.check_password(self.password))

    def test_product_owner_can_edit_but_other_user_cannot(self):
        product = Product.objects.create(seller=self.alice, name="노트북", description="정상 상품", price=1000)
        self.client.force_login(self.bob)
        response = self.client.post(reverse("products:edit", args=[product.public_id]), {
            "name": "변조", "description": "변조", "price": 1, "sale_status": Product.SaleStatus.ON_SALE
        })
        self.assertEqual(response.status_code, 403)
        product.refresh_from_db()
        self.assertEqual(product.name, "노트북")

    def test_hidden_product_is_not_visible_to_other_user(self):
        product = Product.objects.create(
            seller=self.alice, name="숨김", description="숨김", price=100,
            visibility_status=Product.Visibility.HIDDEN,
        )
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(reverse("products:detail", args=[product.public_id])).status_code, 403)

    def test_stored_text_is_escaped_in_product_page(self):
        product = Product.objects.create(seller=self.alice, name="<script>alert(1)</script>", description="<img src=x onerror=alert(1)>", price=100)
        response = self.client.get(reverse("products:detail", args=[product.public_id]))
        self.assertNotContains(response, "<script>alert(1)</script>", html=False)
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;", html=False)

    def test_self_report_is_rejected(self):
        report = Report(reporter=self.alice, reported_user=self.alice, reason="invalid")
        with self.assertRaises(ValidationError):
            report.full_clean()

    @override_settings(PRODUCT_REPORT_THRESHOLD=2)
    def test_report_threshold_moves_product_to_review(self):
        charlie = User.objects.create_user(username="charlie", password=self.password)
        product = Product.objects.create(seller=self.alice, name="의심 상품", description="설명", price=100)
        first = Report.objects.create(reporter=self.bob, reported_product=product, reason="신고1")
        apply_report_threshold(first)
        product.refresh_from_db()
        self.assertEqual(product.visibility_status, Product.Visibility.PUBLIC)
        second = Report.objects.create(reporter=charlie, reported_product=product, reason="신고2")
        apply_report_threshold(second)
        product.refresh_from_db()
        self.assertEqual(product.visibility_status, Product.Visibility.UNDER_REVIEW)
        self.assertTrue(AuditLog.objects.filter(action="AUTO_RESTRICT_PRODUCT").exists())

    def test_transfer_is_atomic_and_idempotent(self):
        key = uuid.uuid4()
        before_alice = self.alice.wallet.balance
        before_bob = self.bob.wallet.balance
        first, created = transfer_points(sender=self.alice, receiver=self.bob, amount=500, idempotency_key=key)
        second, created_again = transfer_points(sender=self.alice, receiver=self.bob, amount=500, idempotency_key=key)
        self.alice.wallet.refresh_from_db()
        self.bob.wallet.refresh_from_db()
        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(self.alice.wallet.balance, before_alice - 500)
        self.assertEqual(self.bob.wallet.balance, before_bob + 500)
        self.assertEqual(PointTransaction.objects.count(), 1)

    def test_failed_transfer_does_not_change_balances(self):
        before_alice = self.alice.wallet.balance
        before_bob = self.bob.wallet.balance
        with self.assertRaises(ValidationError):
            transfer_points(sender=self.alice, receiver=self.bob, amount=before_alice + 1, idempotency_key=uuid.uuid4())
        self.alice.wallet.refresh_from_db()
        self.bob.wallet.refresh_from_db()
        self.assertEqual(self.alice.wallet.balance, before_alice)
        self.assertEqual(self.bob.wallet.balance, before_bob)
        self.assertEqual(PointTransaction.objects.count(), 0)

    def test_direct_chat_is_visible_only_to_participant(self):
        charlie = User.objects.create_user(username="charlie2", password=self.password)
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.DIRECT, direct_key=f"{self.alice.pk}:{self.bob.pk}")
        ChatParticipant.objects.create(room=room, user=self.alice)
        ChatParticipant.objects.create(room=room, user=self.bob)
        self.client.force_login(charlie)
        response = self.client.get(reverse("chat:room", args=[room.public_id]))
        self.assertEqual(response.status_code, 403)

    def test_product_detail_can_start_direct_chat_with_seller(self):
        product = Product.objects.create(seller=self.alice, name="채팅 상품", description="설명", price=1000)
        self.client.force_login(self.bob)
        response = self.client.post(reverse("chat:direct_with_user", args=[product.seller.public_id]))
        room = ChatRoom.objects.get(room_type=ChatRoom.RoomType.DIRECT)
        self.assertRedirects(response, reverse("chat:room", args=[room.public_id]))
        self.assertSetEqual(set(room.participants.values_list("pk", flat=True)), {self.alice.pk, self.bob.pk})

    def test_direct_chat_shortcut_rejects_get(self):
        self.client.force_login(self.bob)
        response = self.client.get(reverse("chat:direct_with_user", args=[self.alice.public_id]))
        self.assertEqual(response.status_code, 405)

    def test_sample_products_are_split_between_three_sellers_per_category(self):
        call_command("seed_sample_data")
        for category in Product.Category.values:
            seller_count = Product.objects.filter(
                category=category,
                sample_image_path__startswith="images/products/",
            ).values("seller_id").distinct().count()
            self.assertEqual(seller_count, 3)

    def test_my_page_shows_only_my_products(self):
        own = Product.objects.create(seller=self.alice, name="내 상품", description="설명", price=1000)
        Product.objects.create(seller=self.bob, name="남의 상품", description="설명", price=2000)
        self.client.force_login(self.alice)
        response = self.client.get(reverse("accounts:me"))
        self.assertContains(response, own.name)
        self.assertNotContains(response, "남의 상품")

    def test_my_page_shows_only_participating_direct_chats(self):
        charlie = User.objects.create_user(username="charlie-chat", password=self.password)
        my_room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.DIRECT, direct_key=f"{self.alice.pk}:{self.bob.pk}")
        ChatParticipant.objects.create(room=my_room, user=self.alice)
        ChatParticipant.objects.create(room=my_room, user=self.bob)
        Message.objects.create(room=my_room, author=self.bob, content="내가 볼 수 있는 최근 메시지")
        other_room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.DIRECT, direct_key=f"{self.bob.pk}:{charlie.pk}")
        ChatParticipant.objects.create(room=other_room, user=self.bob)
        ChatParticipant.objects.create(room=other_room, user=charlie)
        Message.objects.create(room=other_room, author=charlie, content="노출되면 안 되는 메시지")
        self.client.force_login(self.alice)
        response = self.client.get(reverse("accounts:me"))
        self.assertContains(response, "내가 볼 수 있는 최근 메시지")
        self.assertContains(response, reverse("chat:room", args=[my_room.public_id]))
        self.assertNotContains(response, "노출되면 안 되는 메시지")
        self.assertNotContains(response, reverse("chat:room", args=[other_room.public_id]))

    def test_my_page_opens_requested_sidebar_section(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse("accounts:me"), {"section": "chats"})
        self.assertContains(response, 'data-active-section="chats"')

    def test_my_page_rejects_unknown_sidebar_section(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse("accounts:me"), {"section": "unknown"})
        self.assertContains(response, 'data-active-section="overview"')

    def test_my_page_defaults_to_profile_overview(self):
        Product.objects.create(seller=self.alice, category=Product.Category.DIGITAL, name="프로필 상품", description="설명", price=1000)
        self.client.force_login(self.alice)
        response = self.client.get(reverse("accounts:me"))
        self.assertContains(response, 'data-active-section="overview"')
        self.assertContains(response, "MY SELLER PROFILE")
        self.assertContains(response, "디지털/가전 1")

    def test_public_profile_shows_active_categories_and_completed_count(self):
        Product.objects.create(seller=self.alice, category=Product.Category.DIGITAL, name="판매 중", description="설명", price=1000)
        sold = Product.objects.create(seller=self.alice, category=Product.Category.FASHION, name="판매 완료", description="설명", price=2000, sale_status=Product.SaleStatus.SOLD)
        response = self.client.get(reverse("accounts:profile", args=[self.alice.public_id]))
        self.assertContains(response, "디지털/가전 1")
        self.assertContains(response, "거래 완료")
        self.assertContains(response, reverse("accounts:completed_products", args=[self.alice.public_id]))
        history = self.client.get(reverse("accounts:completed_products", args=[self.alice.public_id]))
        self.assertContains(history, sold.name)
        self.assertNotContains(history, "판매 중")

    def test_profile_uses_default_avatar_when_not_uploaded(self):
        response = self.client.get(reverse("accounts:profile", args=[self.alice.public_id]))
        self.assertContains(response, "images/profiles/default-avatar.png")

    def test_user_search_finds_active_user_by_username(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse("accounts:user_search"), {"q": "bob"})
        self.assertContains(response, self.bob.username)
        self.assertContains(response, reverse("accounts:profile", args=[self.bob.public_id]))
        self.assertNotContains(response, "전체 채팅")

    def test_user_search_hides_restricted_users(self):
        self.bob.status = User.Status.RESTRICTED
        self.bob.save(update_fields=["status"])
        self.client.force_login(self.alice)
        response = self.client.get(reverse("accounts:user_search"), {"q": "bob"})
        self.assertNotContains(response, reverse("accounts:profile", args=[self.bob.public_id]))

    def test_user_search_requires_login(self):
        response = self.client.get(reverse("accounts:user_search"))
        self.assertRedirects(response, reverse("accounts:login") + "?next=" + reverse("accounts:user_search"))

    def test_restricted_user_cannot_create_product(self):
        self.alice.status = User.Status.RESTRICTED
        self.alice.save(update_fields=["status"])
        self.client.force_login(self.alice)
        response = self.client.get(reverse("products:create"))
        self.assertEqual(response.status_code, 403)

    def test_logout_rejects_get(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)
