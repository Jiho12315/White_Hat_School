from django.urls import path
from . import views

app_name = "products"
urlpatterns = [
    path("", views.product_list, name="list"),
    path("new/", views.product_create, name="create"),
    path("<uuid:public_id>/", views.product_detail, name="detail"),
    path("<uuid:public_id>/edit/", views.product_edit, name="edit"),
    path("<uuid:public_id>/delete/", views.product_delete, name="delete"),
]
