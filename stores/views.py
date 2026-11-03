
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import User
from .forms import StoreForm
from .models import Store


def approved_seller_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user

        # Vérifier que l'utilisateur est un vendeur
        if user.role != User.Role.SELLER:
            messages.error(
                request,
                "Cette fonctionnalité est réservée aux vendeurs.",
            )
            return redirect("accounts:profile")

        # Vérifier que le compte vendeur est approuvé
        if user.seller_status != User.SellerStatus.APPROVED:
            messages.warning(
                request,
                "Votre compte vendeur doit être approuvé par l'administrateur.",
            )
            return redirect("accounts:profile")

        return view_func(request, *args, **kwargs)

    return wrapper


@login_required
def create_store_view(request):
    # Seuls les vendeurs approuvés peuvent créer une boutique
    if request.user.role != User.Role.SELLER:
        messages.error(
            request,
            "Seuls les vendeurs peuvent créer une boutique.",
        )
        return redirect("accounts:profile")

    if request.user.seller_status != User.SellerStatus.APPROVED:
        messages.warning(
            request,
            "Votre compte vendeur doit être approuvé par l'administrateur.",
        )
        return redirect("accounts:profile")

    # Un vendeur ne peut créer qu'une seule boutique
    if Store.objects.filter(owner=request.user).exists():
        messages.info(
            request,
            "Vous possédez déjà une boutique.",
        )
        return redirect("stores:my_store")

    if request.method == "POST":
        form = StoreForm(request.POST, request.FILES)

        if form.is_valid():
            store = form.save(commit=False)
            store.owner = request.user
            store.status = Store.Status.PENDING
            store.save()

            messages.success(
                request,
                "Votre boutique a été créée et attend la validation de l'administrateur.",
            )
            return redirect("stores:my_store")
    else:
        form = StoreForm()

    return render(
        request,
        "stores/create_store.html",
        {"form": form},
    )


@approved_seller_required
def my_store_view(request):
    # Récupérer uniquement la boutique du vendeur connecté
    store = get_object_or_404(
        Store,
        owner=request.user,
    )

    return render(
        request,
        "stores/my_store.html",
        {"store": store},
    )


@approved_seller_required
def edit_store_view(request):
    # Empêcher l'accès à la boutique d'un autre vendeur
    store = get_object_or_404(
        Store,
        owner=request.user,
    )

    if request.method == "POST":
        form = StoreForm(
            request.POST,
            request.FILES,
            instance=store,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Les informations de votre boutique ont été mises à jour.",
            )
            return redirect("stores:my_store")
    else:
        form = StoreForm(instance=store)

    return render(
        request,
        "stores/edit_store.html",
        {
            "form": form,
            "store": store,
        },
    )
