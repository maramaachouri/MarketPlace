
from django.urls import path

from . import views

app_name = "stores"

urlpatterns = [
    path("create/", views.create_store_view, name="create"),
    path("my-store/", views.my_store_view, name="my_store"),
    path("edit/", views.edit_store_view, name="edit"),
]
