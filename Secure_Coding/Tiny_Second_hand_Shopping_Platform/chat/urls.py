from django.urls import path
from . import views

app_name = "chat"
urlpatterns = [
    path("global/", views.global_chat, name="global"),
    path("direct/new/", views.direct_create, name="direct_create"),
    path("direct/users/<uuid:public_id>/", views.direct_with_user, name="direct_with_user"),
    path("rooms/<uuid:public_id>/", views.room_detail, name="room"),
    path("rooms/<uuid:public_id>/transfer/", views.room_transfer, name="room_transfer"),
]
