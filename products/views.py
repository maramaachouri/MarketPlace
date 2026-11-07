from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.models import User
from stores.models import Store
from stores.views import approved_seller_required

from .forms import ProductFilterForm, ProductForm, ReviewForm
from .models import Favorite, Product, Review


def client_required(view_func):
    """Réserve une vue aux clients connectés (favoris, avis)."""

    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.CLIENT:
            messages.warning(request, "Cette fonctionnalité est réservée aux clients.")
            return redirect("products:home")
        return view_func(request, *args, **kwargs)

    return wrapper


# ---------- PARTIE PUBLIQUE (catalogue) ----------

def home_view(request):
    products = (
        Product.objects
        .filter(is_active=True)
        .select_related("store", "category")
        .annotate(avg_rating=Avg("reviews__rating"), review_count=Count("reviews"))
    )

    form = ProductFilterForm(request.GET)
    if form.is_valid():
        q = form.cleaned_data["q"]
        category = form.cleaned_data["category"]
        min_price = form.cleaned_data["min_price"]
        max_price = form.cleaned_data["max_price"]

        if q:
            products = products.filter(
                Q(name__icontains=q) | Q(description__icontains=q)
            )
        if category:
            products = products.filter(category=category)
        if min_price is not None:
            products = products.filter(price__gte=min_price)
        if max_price is not None:
            products = products.filter(price__lte=max_price)

    return render(
        request,
        "products/product_list.html",
        {"products": products, "form": form},
    )


def product_detail_view(request, pk):
    product = get_object_or_404(
        Product.objects.select_related("store", "category"),
        pk=pk,
        is_active=True,
    )

    user = request.user
    is_client = user.is_authenticated and user.role == User.Role.CLIENT
    user_review = None
    is_favorite = False
    review_form = None

    if is_client:
        user_review = product.reviews.filter(user=user).first()
        is_favorite = Favorite.objects.filter(user=user, product=product).exists()

    if request.method == "POST":
        # Envoi du formulaire d'avis
        if not user.is_authenticated:
            return redirect("accounts:login")
        if not is_client:
            messages.warning(request, "Seuls les clients peuvent laisser un avis.")
            return redirect("products:detail", pk=product.pk)

        review_form = ReviewForm(request.POST, instance=user_review)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.user = user
            review.product = product
            review.save()
            messages.success(request, "Votre avis a été enregistré.")
            return redirect("products:detail", pk=product.pk)
    elif is_client:
        review_form = ReviewForm(instance=user_review)

    reviews = product.reviews.select_related("user")
    stats = reviews.aggregate(avg=Avg("rating"), count=Count("id"))

    return render(
        request,
        "products/product_detail.html",
        {
            "product": product,
            "reviews": reviews,
            "avg_rating": stats["avg"],
            "review_count": stats["count"],
            "review_form": review_form,
            "user_review": user_review,
            "is_client": is_client,
            "is_favorite": is_favorite,
        },
    )


@client_required
@require_POST
def review_delete_view(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)
    product_pk = review.product_id
    review.delete()
    messages.success(request, "Votre avis a été supprimé.")
    return redirect("products:detail", pk=product_pk)


# ---------- FAVORIS ----------

@client_required
@require_POST
def favorite_toggle_view(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)

    if created:
        messages.success(request, "Produit ajouté à vos favoris.")
    else:
        favorite.delete()
        messages.info(request, "Produit retiré de vos favoris.")

    # Retour à la page d'où l'on vient (seulement si l'adresse est sûre)
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("products:detail", pk=product.pk)


@client_required
def favorites_view(request):
    favorites = (
        Favorite.objects
        .filter(user=request.user, product__is_active=True)
        .select_related("product__store", "product__category")
    )
    return render(request, "products/favorites.html", {"favorites": favorites})


# ---------- PARTIE VENDEUR ----------

def _get_seller_store(request):
    """Renvoie la boutique du vendeur connecté, ou None s'il n'en a pas."""
    return Store.objects.filter(owner=request.user).first()


@approved_seller_required
def my_products_view(request):
    store = _get_seller_store(request)
    if store is None:
        messages.warning(request, "Créez d'abord votre boutique pour ajouter des produits.")
        return redirect("stores:create")

    products = store.products.select_related("category")
    return render(request, "products/my_products.html", {"products": products, "store": store})


@approved_seller_required
def product_create_view(request):
    store = _get_seller_store(request)
    if store is None:
        messages.warning(request, "Créez d'abord votre boutique pour ajouter des produits.")
        return redirect("stores:create")

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.store = store
            product.save()
            messages.success(request, "Produit ajouté avec succès.")
            return redirect("products:my_products")
    else:
        form = ProductForm()

    return render(request, "products/product_form.html", {"form": form, "title": "Ajouter un produit"})


@approved_seller_required
def product_update_view(request, pk):
    store = _get_seller_store(request)
    # store=store : un vendeur ne peut modifier QUE ses propres produits
    product = get_object_or_404(Product, pk=pk, store=store)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit modifié avec succès.")
            return redirect("products:my_products")
    else:
        form = ProductForm(instance=product)

    return render(request, "products/product_form.html", {"form": form, "title": "Modifier le produit"})


@approved_seller_required
def product_delete_view(request, pk):
    store = _get_seller_store(request)
    product = get_object_or_404(Product, pk=pk, store=store)

    if request.method == "POST":
        product.delete()
        messages.success(request, "Produit supprimé.")
        return redirect("products:my_products")

    return render(request, "products/product_confirm_delete.html", {"product": product})