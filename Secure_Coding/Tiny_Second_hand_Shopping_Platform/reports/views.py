from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render

from core.security import active_user_required, rate_limited
from products.models import Product
from .forms import ReportForm
from .services import apply_report_threshold


@active_user_required
def report_create(request, product_public_id=None):
    product = None
    if product_public_id is not None:
        product = get_object_or_404(Product.objects.select_related("seller"), public_id=product_public_id)
    initial = {"target_type": request.GET.get("type", ""), "target_id": request.GET.get("id", "")}
    form = ReportForm(request.POST or None, initial=initial, reporter=request.user, reported_product=product)
    if request.method == "POST":
        if rate_limited("report", request.user.pk):
            messages.error(request, "신고 요청이 너무 많습니다. 잠시 후 다시 시도하세요.")
            return render(request, "reports/form.html", {"form": form}, status=429)
        if form.is_valid():
            try:
                with transaction.atomic():
                    report = form.save()
                    apply_report_threshold(report, request)
            except IntegrityError:
                form.add_error(None, "이미 신고한 대상입니다.")
            else:
                messages.success(request, "신고가 접수되었습니다.")
                return redirect("core:home")
    return render(request, "reports/form.html", {"form": form, "reported_product": product})
