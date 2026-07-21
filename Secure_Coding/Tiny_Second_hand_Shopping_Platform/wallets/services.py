from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import User
from .models import PointTransaction, Wallet


@transaction.atomic
def transfer_points(*, sender, receiver, amount, idempotency_key):
    existing = PointTransaction.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        if existing.sender_id != sender.id:
            raise ValidationError("유효하지 않은 중복 요청입니다.")
        return existing, False
    if sender.pk == receiver.pk:
        raise ValidationError("자기 자신에게 송금할 수 없습니다.")
    if not sender.can_write or not receiver.can_write:
        raise ValidationError("정상 상태의 사용자 사이에서만 송금할 수 있습니다.")
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        raise ValidationError("유효한 금액을 입력하세요.")
    if amount <= 0:
        raise ValidationError("송금액은 0보다 커야 합니다.")

    user_ids = sorted([sender.pk, receiver.pk])
    locked = {w.user_id: w for w in Wallet.objects.select_for_update().filter(user_id__in=user_ids).order_by("user_id")}
    if len(locked) != 2:
        raise ValidationError("지갑 정보를 찾을 수 없습니다.")
    sender_wallet, receiver_wallet = locked[sender.pk], locked[receiver.pk]
    if sender_wallet.balance < amount:
        raise ValidationError("잔액이 부족합니다.")
    sender_wallet.balance -= amount
    receiver_wallet.balance += amount
    sender_wallet.save(update_fields=["balance", "updated_at"])
    receiver_wallet.save(update_fields=["balance", "updated_at"])
    tx = PointTransaction.objects.create(
        idempotency_key=idempotency_key, sender=sender, receiver=receiver, amount=amount
    )
    return tx, True
