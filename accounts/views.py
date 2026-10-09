from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User


def register_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():

            return render(
                request,
                "accounts/register.html",
                {
                    "error": "এই username আগে থেকেই আছে।"
                }
            )

        user = User.objects.create_user(
            username=username,
            password=password
        )

        login(request, user)

        return redirect("/")

    return render(
        request,
        "accounts/register.html"
    )


def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("/")

        return render(
            request,
            "accounts/login.html",
            {
                "error": "Username অথবা password ভুল।"
            }
        )

    return render(
        request,
        "accounts/login.html"
    )


def logout_view(request):

    logout(request)

    return redirect("/accounts/login/")


def home_view(request):

    if not request.user.is_authenticated:
        return redirect("/accounts/login/")

    return render(
        request,
        "home.html"
    )