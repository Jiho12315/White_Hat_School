from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from PIL import Image, UnidentifiedImageError

from .models import User


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("avatar", "bio")

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if not avatar or not hasattr(avatar, "size"):
            return avatar
        if avatar.size > settings.MAX_IMAGE_BYTES:
            raise forms.ValidationError("프로필 이미지 크기가 허용 범위를 초과합니다.")
        try:
            parsed = Image.open(avatar)
            parsed.verify()
            avatar.seek(0)
        except (UnidentifiedImageError, OSError):
            raise forms.ValidationError("유효한 프로필 이미지 파일이 아닙니다.")
        if parsed.format not in settings.ALLOWED_IMAGE_FORMATS:
            raise forms.ValidationError("JPEG, PNG, WEBP 이미지만 사용할 수 있습니다.")
        return avatar
