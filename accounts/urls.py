from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("register/",views.register,name = "register"),
    path("logout/",auth_views.LogoutView.as_view(),name = "logout"),
    path("login/",views.RoleBasedLoginView.as_view(),name="login"),
    path("profile/", views.profile_view, name='profile'),
    path("profile/edit/", views.edit_profile, name='edit_profile'),
]