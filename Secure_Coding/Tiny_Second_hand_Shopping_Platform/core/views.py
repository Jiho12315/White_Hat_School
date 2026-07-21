from django.shortcuts import render
from products.models import Product


def home(request):
    products = Product.objects.filter(visibility_status=Product.Visibility.PUBLIC).select_related("seller")[:8]
    return render(request, "core/home.html", {"products": products})
