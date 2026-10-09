from django.contrib import admin
from django.urls import path, include

from accounts.views import home_view


urlpatterns = [

    path(
        "admin/",
        admin.site.urls
    ),

    path(
        "accounts/",
        include("accounts.urls")
    ),

    path(
        "api/",
        include("chat.urls")
    ),

    path(
        "",
        home_view,
        name="home"
    ),
]