from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


def client_ip(request):
    return request.META.get("REMOTE_ADDR")


def rate_limited(scope, identity):
    limit, window = settings.RATE_LIMITS[scope]
    key = f"rate:{scope}:{identity}"
    count = cache.get(key, 0)
    if count >= limit:
        return True
    if count == 0:
        cache.set(key, 1, window)
    else:
        cache.incr(key)
    return False


def active_user_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        if not request.user.can_write:
            messages.error(request, "현재 계정은 이 기능을 사용할 수 없습니다.")
            return HttpResponseForbidden("계정 상태로 인해 요청이 거부되었습니다.")
        return view(request, *args, **kwargs)
    return wrapped
