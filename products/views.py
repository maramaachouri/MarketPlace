from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from stores.models import Store
from stores.views import approved_seller_required

from .forms import ProductFilterForm, ProductForm
from .models import Product


# ---------- PARTIE PUBLIQUE (catalogue) ----------

def home_view(request):
    products = (
        Product.objects
        .filter(is_active=True)
        .select_related("store", "category")
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
    return render(request, "products/product_detail.html", {"product": product})


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