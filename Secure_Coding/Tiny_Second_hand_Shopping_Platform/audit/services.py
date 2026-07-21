from .models import AuditLog


def record_audit(*, actor, action, target, result="SUCCESS", request=None, detail=None):
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        target_type=target.__class__.__name__,
        target_public_id=str(getattr(target, "public_id", getattr(target, "pk", ""))),
        result=result,
        detail=detail or {},
        ip_address=request.META.get("REMOTE_ADDR") if request else None,
    )
