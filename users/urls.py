from django.urls import path

from .views import BanUserView, MeView, RegisterView, UserListView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("", UserListView.as_view(), name="user-list"),
    path("<uuid:pk>/ban/", BanUserView.as_view(), name="ban-user"),
]
