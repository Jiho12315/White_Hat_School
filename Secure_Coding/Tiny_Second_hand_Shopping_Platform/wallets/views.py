from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from audit.services import record_audit
from core.security import active_user_required, rate_limited
from .forms import TransferForm
from .services import transfer_points


@active_user_required
def transfer(request):
    form = TransferForm(request.POST or None)
    if request.method == "POST":
        if rate_limited("transfer", request.user.pk):
            messages.error(request, "송금 요청이 너무 많습니다. 잠시 후 다시 시도하세요.")
            return render(request, "wallets/transfer.html", {"form": form}, status=429)
        if form.is_valid():
            try:
                tx, created = transfer_points(
                    sender=request.user,
                    receiver=form.cleaned_data["receiver"],
                    amount=form.cleaned_data["amount"],
                    idempotency_key=form.cleaned_data["idempotency_key"],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                record_audit(actor=request.user, action="POINT_TRANSFER", target=tx, request=request, detail={"created": created, "amount": tx.amount})
                messages.success(request, "송금이 완료되었습니다." if created else "이미 처리된 송금 요청입니다.")
                return redirect("accounts:me")
    return render(request, "wallets/transfer.html", {"form": form})
