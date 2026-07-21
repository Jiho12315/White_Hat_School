from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator

from core.security import active_user_required
from .forms import ProductForm
from .models import Product
from reports.models import Report


def product_list(request):
    products = Product.objects.filter(visibility_status=Product.Visibility.PUBLIC).select_related("seller")
    query = request.GET.get("q", "").strip()[:120]
    category = request.GET.get("category", "").strip()
    valid_categories = {value for value, _ in Product.Category.choices}
    if category in valid_categories:
        products = products.filter(category=category)
    else:
        category = ""
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    page = Paginator(products, 12).get_page(request.GET.get("page"))
    return render(request, "products/list.html", {
        "page": page,
        "query": query,
        "selected_category": category,
        "categories": Product.Category.choices,
    })


def product_detail(request, public_id):
    product = get_object_or_404(Product.objects.select_related("seller"), public_id=public_id)
    if product.visibility_status != Product.Visibility.PUBLIC and not (request.user.is_authenticated and (request.user == product.seller or request.user.is_staff)):
        return HttpResponseForbidden("공개되지 않은 상품입니다.")
    has_reported = request.user.is_authenticated and Report.objects.filter(
        reporter=request.user,
        reported_product=product,
    ).exists()
    return render(request, "products/detail.html", {"product": product, "has_reported": has_reported})


@active_user_required
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.seller = request.user
        product.save()
        messages.success(request, "상품을 등록했습니다.")
        return redirect("products:detail", public_id=product.public_id)
    return render(request, "products/form.html", {"form": form, "title": "상품 등록"})


@active_user_required
def product_edit(request, public_id):
    product = get_object_or_404(Product, public_id=public_id)
    if request.user != product.seller and not request.user.is_staff:
        return HttpResponseForbidden("수정 권한이 없습니다.")
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "상품을 수정했습니다.")
        return redirect("products:detail", public_id=product.public_id)
    return render(request, "products/form.html", {"form": form, "title": "상품 수정"})


@active_user_required
def product_delete(request, public_id):
    if request.method != "POST":
        return HttpResponseForbidden("POST 요청만 허용됩니다.")
    product = get_object_or_404(Product, public_id=public_id)
    if request.user != product.seller and not request.user.is_staff:
        return HttpResponseForbidden("삭제 권한이 없습니다.")
    product.visibility_status = Product.Visibility.DELETED
    product.save(update_fields=["visibility_status", "updated_at"])
    messages.success(request, "상품을 삭제했습니다.")
    return redirect("products:list")
