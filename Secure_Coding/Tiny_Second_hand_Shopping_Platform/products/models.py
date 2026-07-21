import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


def product_image_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "img"
    return f"products/{instance.public_id}/{uuid.uuid4().hex}.{extension}"


class Product(models.Model):
    class Category(models.TextChoices):
        DIGITAL = "DIGITAL", "디지털/가전"
        FASHION = "FASHION", "의류/잡화"
        LIVING = "LIVING", "생활/주방"
        HOBBY = "HOBBY", "도서/티켓/취미"
        SPORTS = "SPORTS", "스포츠/레저"
        BEAUTY = "BEAUTY", "뷰티/미용"
        ETC = "ETC", "기타 중고"

    class SaleStatus(models.TextChoices):
        ON_SALE = "ON_SALE", "판매 중"
        RESERVED = "RESERVED", "예약"
        SOLD = "SOLD", "판매 완료"

    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "공개"
        UNDER_REVIEW = "UNDER_REVIEW", "검토 중"
        HIDDEN = "HIDDEN", "숨김"
        DELETED = "DELETED", "삭제"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="products")
    category = models.CharField(max_length=12, choices=Category.choices, default=Category.ETC, db_index=True)
    name = models.CharField(max_length=120, db_index=True)
    description = models.TextField(max_length=3000)
    price = models.PositiveBigIntegerField(validators=[MinValueValidator(1), MaxValueValidator(1_000_000_000_000)])
    image = models.ImageField(upload_to=product_image_path, blank=True)
    sample_image_path = models.CharField(max_length=255, blank=True, editable=False)
    sale_status = models.CharField(max_length=12, choices=SaleStatus.choices, default=SaleStatus.ON_SALE, db_index=True)
    visibility_status = models.CharField(max_length=16, choices=Visibility.choices, default=Visibility.PUBLIC, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["visibility_status", "-created_at"])]

    def __str__(self):
        return self.name

    @property
    def category_preview_path(self):
        paths = {
            self.Category.DIGITAL: "images/categories/digital.png",
            self.Category.FASHION: "images/categories/fashion.png",
            self.Category.LIVING: "images/categories/living.png",
            self.Category.HOBBY: "images/categories/hobby.png",
            self.Category.SPORTS: "images/categories/sports.png",
            self.Category.BEAUTY: "images/categories/beauty.png",
            self.Category.ETC: "images/categories/etc.png",
        }
        return paths[self.category]
