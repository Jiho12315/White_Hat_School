from django.urls import path
from .views import report_create

app_name = "reports"
urlpatterns = [path("new/", report_create, name="create")]
urlpatterns += [path("products/<uuid:product_public_id>/new/", report_create, name="product_create")]
