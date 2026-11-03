
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import RegisterForm, LoginForm, ProfileUpdateForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                "Votre compte a été créé avec succès. Vous pouvez vous connecter."
            )
            return redirect("accounts:login")
    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(
                request,
                f"Bienvenue {user.first_name or user.username} !"
            )
            return redirect("accounts:profile")
    else:
        form = LoginForm(request)

    return render(
        request,
        "accounts/login.html",
        {"form": form},
    )


@login_required
def profile_view(request):
    return render(
        request,
        "accounts/profile.html",
    )


def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "Vous êtes déconnecté(e).")
        return redirect("accounts:login")

    return redirect("accounts:profile")

@login_required
def edit_profile_view(request):

    if request.method == "POST":
        form = ProfileUpdateForm(
            request.POST,
            instance=request.user
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Votre profil a été mis à jour avec succès."
            )
            return redirect("accounts:profile")

    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(
        request,
        "accounts/edit_profile.html",
        {"form": form}
    )