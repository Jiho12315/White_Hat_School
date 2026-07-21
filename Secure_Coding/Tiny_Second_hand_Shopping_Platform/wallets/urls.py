from django.urls import path
from .views import transfer

app_name = "wallets"
urlpatterns = [path("transfer/", transfer, name="transfer")]
