from django.urls import path
from . import views

app_name = "accounts"
urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.SafeLoginView.as_view(), name="login"),
    path("logout/", views.SafeLogoutView.as_view(), name="logout"),
    path("me/", views.my_page, name="me"),
    path("users/", views.user_search, name="user_search"),
    path("users/<uuid:public_id>/", views.public_profile, name="profile"),
    path("users/<uuid:public_id>/completed/", views.completed_products, name="completed_products"),
]
