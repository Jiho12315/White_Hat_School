import uuid

from django import forms

from accounts.models import User


class DirectChatForm(forms.Form):
    username = forms.CharField(max_length=150, label="대화 상대 계정명")

    def __init__(self, *args, sender, **kwargs):
        self.sender = sender
        super().__init__(*args, **kwargs)

    def clean_username(self):
        try:
            user = User.objects.get(username=self.cleaned_data["username"])
        except User.DoesNotExist:
            raise forms.ValidationError("사용자를 찾을 수 없습니다.")
        if user == self.sender:
            raise forms.ValidationError("자기 자신과 1:1 채팅을 만들 수 없습니다.")
        if not user.can_write:
            raise forms.ValidationError("대화할 수 없는 사용자입니다.")
        return user


class ChatTransferForm(forms.Form):
    amount = forms.IntegerField(
        min_value=1,
        label="송금 금액",
        widget=forms.NumberInput(attrs={"placeholder": "금액 입력", "min": 1, "inputmode": "numeric"}),
    )
    idempotency_key = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial["idempotency_key"] = uuid.uuid4()
