from django import forms
from django.conf import settings
from PIL import Image, UnidentifiedImageError

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("category", "name", "description", "price", "image", "sale_status")

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if not image or not hasattr(image, "size"):
            return image
        if image.size > settings.MAX_IMAGE_BYTES:
            raise forms.ValidationError("이미지 크기가 허용 범위를 초과합니다.")
        try:
            parsed = Image.open(image)
            parsed.verify()
            image.seek(0)
        except (UnidentifiedImageError, OSError):
            raise forms.ValidationError("유효한 이미지 파일이 아닙니다.")
        if parsed.format not in settings.ALLOWED_IMAGE_FORMATS:
            raise forms.ValidationError("허용되지 않은 이미지 형식입니다.")
        return image
