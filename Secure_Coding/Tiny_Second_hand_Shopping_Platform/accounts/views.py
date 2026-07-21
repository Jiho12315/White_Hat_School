from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404, redirect, render

from core.security import client_ip, rate_limited
from .forms import ProfileForm, SignUpForm
from .models import User
from chat.models import ChatRoom, Message
from products.models import Product
from reports.models import Report
from wallets.models import PointTransaction


def signup(request):
    if request.user.is_authenticated:
        return redirect("core:home")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        request.session.cycle_key()
        messages.success(request, "회원가입이 완료되었습니다.")
        return redirect("core:home")
    return render(request, "accounts/signup.html", {"form": form})


class SafeLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = AuthenticationForm

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username", "")[:150].lower()
        if rate_limited("login", f"{client_ip(request)}:{username}"):
            messages.error(request, "로그인 요청이 너무 많습니다. 잠시 후 다시 시도하세요.")
            return render(request, self.template_name, {"form": self.get_form()}, status=429)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session.cycle_key()
        return response


class SafeLogoutView(LogoutView):
    http_method_names = ["post"]


def public_profile(request, public_id):
    user = get_object_or_404(User, public_id=public_id)
    active_products = user.products.filter(
        visibility_status=Product.Visibility.PUBLIC,
        sale_status__in=[Product.SaleStatus.ON_SALE, Product.SaleStatus.RESERVED],
    )
    active_categories = active_products.values("category").annotate(count=Count("id")).order_by("category")
    category_labels = dict(Product.Category.choices)
    category_summary = [
        {"label": category_labels[item["category"]], "count": item["count"]}
        for item in active_categories
    ]
    completed_count = user.products.filter(
        visibility_status=Product.Visibility.PUBLIC,
        sale_status=Product.SaleStatus.SOLD,
    ).count()
    return render(request, "accounts/profile.html", {
        "profile_user": user,
        "active_products": active_products[:6],
        "active_product_count": active_products.count(),
        "category_summary": category_summary,
        "completed_count": completed_count,
    })


def completed_products(request, public_id):
    profile_user = get_object_or_404(User, public_id=public_id)
    products = profile_user.products.filter(
        visibility_status=Product.Visibility.PUBLIC,
        sale_status=Product.SaleStatus.SOLD,
    ).order_by("-updated_at")
    return render(request, "accounts/completed_products.html", {
        "profile_user": profile_user,
        "completed_products": products,
    })


@login_required
def user_search(request):
    query = request.GET.get("q", "").strip()[:150]
    users = User.objects.filter(status=User.Status.ACTIVE).annotate(
        active_product_count=Count(
            "products",
            filter=Q(
                products__visibility_status=Product.Visibility.PUBLIC,
                products__sale_status__in=[Product.SaleStatus.ON_SALE, Product.SaleStatus.RESERVED],
            ),
            distinct=True,
        ),
        completed_product_count=Count(
            "products",
            filter=Q(
                products__visibility_status=Product.Visibility.PUBLIC,
                products__sale_status=Product.SaleStatus.SOLD,
            ),
            distinct=True,
        ),
    )
    if query:
        users = users.filter(Q(username__icontains=query) | Q(bio__icontains=query))
    users = users.order_by("username")[:50]
    return render(request, "accounts/user_search.html", {"query": query, "users": users})


def my_page(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    profile_form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user, prefix="profile")
    password_form = PasswordChangeForm(request.user, request.POST or None, prefix="password")
    allowed_sections = {"overview", "products", "chats", "reports", "points", "profile", "password"}
    active_section = request.GET.get("section", "overview")
    if active_section not in allowed_sections:
        active_section = "overview"
    if request.method == "POST":
        action = request.POST.get("action")
        if action in {"profile", "password"}:
            active_section = action
        if action == "profile" and profile_form.is_valid():
            profile_form.save()
            messages.success(request, "프로필을 변경했습니다.")
            return redirect("accounts:me")
        if action == "password" and password_form.is_valid():
            password_form.save()
            request.session.flush()
            messages.success(request, "비밀번호가 변경되었습니다. 다시 로그인하세요.")
            return redirect("accounts:login")
    transactions = PointTransaction.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).select_related("sender", "receiver")[:20]
    my_products = request.user.products.exclude(
        visibility_status=Product.Visibility.DELETED,
    ).order_by("-created_at")
    active_products = my_products.filter(
        visibility_status=Product.Visibility.PUBLIC,
        sale_status__in=[Product.SaleStatus.ON_SALE, Product.SaleStatus.RESERVED],
    )
    active_categories = active_products.values("category").annotate(count=Count("id")).order_by("category")
    category_labels = dict(Product.Category.choices)
    category_summary = [
        {"label": category_labels[item["category"]], "count": item["count"]}
        for item in active_categories
    ]
    completed_count = my_products.filter(
        visibility_status=Product.Visibility.PUBLIC,
        sale_status=Product.SaleStatus.SOLD,
    ).count()
    latest_message = Message.objects.filter(room=OuterRef("pk")).order_by("-created_at")
    chat_rooms = request.user.chat_rooms.filter(
        room_type=ChatRoom.RoomType.DIRECT,
    ).prefetch_related("participants").annotate(
        last_message_content=Subquery(latest_message.values("content")[:1]),
        last_message_at=Subquery(latest_message.values("created_at")[:1]),
    ).order_by("-last_message_at", "-created_at")
    submitted_reports = Report.objects.filter(reporter=request.user).select_related(
        "reported_product", "reported_product__seller", "reported_user"
    ).order_by("-created_at")
    return render(request, "accounts/me.html", {
        "profile_form": profile_form,
        "password_form": password_form,
        "transactions": transactions,
        "my_products": my_products,
        "active_products": active_products[:6],
        "active_product_count": active_products.count(),
        "category_summary": category_summary,
        "completed_count": completed_count,
        "chat_rooms": chat_rooms,
        "submitted_reports": submitted_reports,
        "active_section": active_section,
    })
