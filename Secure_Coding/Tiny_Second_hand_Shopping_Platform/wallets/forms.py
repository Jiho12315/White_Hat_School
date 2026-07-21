import uuid
from django import forms

from accounts.models import User


class TransferForm(forms.Form):
    receiver = forms.CharField(max_length=150, label="받는 사용자 계정명")
    amount = forms.IntegerField(min_value=1, label="금액")
    idempotency_key = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial["idempotency_key"] = uuid.uuid4()

    def clean_receiver(self):
        try:
            return User.objects.get(username=self.cleaned_data["receiver"])
        except User.DoesNotExist:
            raise forms.ValidationError("사용자를 찾을 수 없습니다.")
