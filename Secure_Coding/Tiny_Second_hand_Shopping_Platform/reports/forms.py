from django import forms

from accounts.models import User
from products.models import Product
from .models import Report


class ReportForm(forms.ModelForm):
    target_type = forms.ChoiceField(choices=(("user", "사용자"), ("product", "상품")), required=False)
    target_id = forms.UUIDField(required=False)

    class Meta:
        model = Report
        fields = ("reason_category", "reason")
        labels = {"reason_category": "신고 이유", "reason": "자세한 내용"}
        help_texts = {"reason": "문제가 되는 내용과 확인에 필요한 정보를 구체적으로 작성해 주세요."}
        widgets = {"reason": forms.Textarea(attrs={"rows": 6, "maxlength": 1000, "placeholder": "예: 상품 설명과 실제 상태가 다르며, 판매자가 허위 정보를 안내했습니다."})}

    def __init__(self, *args, reporter, reported_product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.reporter = reporter
        self.reported_product = reported_product
        if reported_product is not None:
            self.fields.pop("target_type")
            self.fields.pop("target_id")

    def clean(self):
        data = super().clean()
        if self.reported_product is not None:
            self.instance.reported_product = self.reported_product
            target_type = target_id = None
        else:
            target_type, target_id = data.get("target_type"), data.get("target_id")
            if not target_type or not target_id:
                raise forms.ValidationError("신고 대상을 확인할 수 없습니다.")
        if self.reported_product is None and target_type == "user":
            target = User.objects.filter(public_id=target_id).first()
            if not target:
                raise forms.ValidationError("신고 대상을 찾을 수 없습니다.")
            self.instance.reported_user = target
        elif self.reported_product is None and target_type == "product":
            target = Product.objects.filter(public_id=target_id).first()
            if not target:
                raise forms.ValidationError("신고 대상을 찾을 수 없습니다.")
            self.instance.reported_product = target
        self.instance.reporter = self.reporter
        try:
            self.instance.clean()
        except Exception as exc:
            raise forms.ValidationError(exc.messages if hasattr(exc, "messages") else str(exc))
        duplicate = Report.objects.filter(reporter=self.reporter)
        duplicate = duplicate.filter(reported_user=self.instance.reported_user) if self.instance.reported_user_id else duplicate.filter(reported_product=self.instance.reported_product)
        if duplicate.exists():
            raise forms.ValidationError("이미 신고한 대상입니다.")
        return data
