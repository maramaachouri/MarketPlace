from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    # Public
    path("", views.home_view, name="home"),
    path("product/<int:pk>/", views.product_detail_view, name="detail"),

    # Vendeur
    path("my-products/", views.my_products_view, name="my_products"),
    path("my-products/add/", views.product_create_view, name="create"),
    path("my-products/<int:pk>/edit/", views.product_update_view, name="update"),
    path("my-products/<int:pk>/delete/", views.product_delete_view, name="delete"),
]