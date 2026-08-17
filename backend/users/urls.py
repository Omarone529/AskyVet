from django.urls import path

from .views import (
    AdminCreateView,
    BanUserView,
    MeView,
    MuteUserView,
    RegisterView,
    UserListView,
)

urlpatterns = [
    # Literal segments first — the UUID converter would not swallow them, but
    # keeping the order explicit documents the intent.
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("admins/", AdminCreateView.as_view(), name="admin-create"),
    path("", UserListView.as_view(), name="user-list"),
    # Moderation
    path("<uuid:pk>/ban/", BanUserView.as_view(), name="ban-user"),
    path("<uuid:pk>/mute/", MuteUserView.as_view(), name="mute-user"),
]
