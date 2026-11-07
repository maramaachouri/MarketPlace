import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import User
from stores.models import Store

from .forms import ProductFilterForm, ProductForm
from .models import Category, Favorite, Product, Review


def make_image():
    """Crée une petite image en mémoire pour tester l'upload."""
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buffer, "PNG")
    return SimpleUploadedFile("test.png", buffer.getvalue(), content_type="image/png")


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class BaseTestCase(TestCase):
    """Prépare des utilisateurs, des boutiques et des produits réutilisables."""

    def setUp(self):
        self.seller1 = User.objects.create_user(
            "seller1", "s1@test.com", "pass12345",
            role=User.Role.SELLER, seller_status=User.SellerStatus.APPROVED,
        )
        self.seller2 = User.objects.create_user(
            "seller2", "s2@test.com", "pass12345",
            role=User.Role.SELLER, seller_status=User.SellerStatus.APPROVED,
        )
        self.pending_seller = User.objects.create_user(
            "pending", "p@test.com", "pass12345",
            role=User.Role.SELLER, seller_status=User.SellerStatus.PENDING,
        )
        self.client_user = User.objects.create_user(
            "client1", "c1@test.com", "pass12345", role=User.Role.CLIENT
        )

        self.store1 = Store.objects.create(owner=self.seller1, name="Boutique 1", description="d")
        self.store2 = Store.objects.create(owner=self.seller2, name="Boutique 2", description="d")

        self.phones = Category.objects.create(name="Téléphones")
        self.clothes = Category.objects.create(name="Vêtements")

        self.galaxy = Product.objects.create(
            store=self.store1, category=self.phones, name="Galaxy S26",
            description="Un super téléphone", price=900, stock=5,
        )
        self.dress = Product.objects.create(
            store=self.store2, category=self.clothes, name="Robe rouge",
            description="Une belle robe", price=50, stock=0,
        )

    def login(self, username):
        self.client.login(username=username, password="pass12345")


# ---------- MODÈLES ----------

class ModelTests(BaseTestCase):
    def test_category_slug_is_generated(self):
        self.assertEqual(self.phones.slug, "telephones")

    def test_product_str(self):
        self.assertEqual(str(self.galaxy), "Galaxy S26")

    def test_product_is_linked_to_store_and_category(self):
        self.assertIn(self.galaxy, self.store1.products.all())
        self.assertIn(self.galaxy, self.phones.products.all())

    def test_deleting_category_keeps_product(self):
        self.phones.delete()
        self.galaxy.refresh_from_db()
        self.assertIsNone(self.galaxy.category)

    def test_deleting_store_deletes_products(self):
        self.store1.delete()
        self.assertFalse(Product.objects.filter(pk=self.galaxy.pk).exists())

    def test_cannot_favorite_twice(self):
        Favorite.objects.create(user=self.client_user, product=self.galaxy)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Favorite.objects.create(user=self.client_user, product=self.galaxy)

    def test_cannot_review_twice(self):
        Review.objects.create(user=self.client_user, product=self.galaxy, rating=4)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Review.objects.create(user=self.client_user, product=self.galaxy, rating=5)


# ---------- FORMULAIRES ----------

class FormTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.valid_data = {
            "category": self.phones.pk, "name": "Casque audio", "description": "Bon son",
            "price": "99.90", "stock": "3", "is_active": "on",
        }

    def test_product_form_valid(self):
        self.assertTrue(ProductForm(self.valid_data).is_valid())

    def test_product_form_rejects_negative_price(self):
        form = ProductForm({**self.valid_data, "price": "-5"})
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_product_form_rejects_zero_price(self):
        self.assertFalse(ProductForm({**self.valid_data, "price": "0"}).is_valid())

    def test_product_form_rejects_short_name(self):
        form = ProductForm({**self.valid_data, "name": "ab"})
        self.assertIn("name", form.errors)

    def test_filter_form_rejects_min_greater_than_max(self):
        form = ProductFilterForm({"min_price": "500", "max_price": "10"})
        self.assertFalse(form.is_valid())

    def test_filter_form_all_fields_optional(self):
        self.assertTrue(ProductFilterForm({}).is_valid())


# ---------- CATALOGUE PUBLIC ----------

class CatalogTests(BaseTestCase):
    def test_home_page_shows_products(self):
        response = self.client.get(reverse("products:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Galaxy S26")
        self.assertContains(response, "Robe rouge")

    def test_inactive_product_is_hidden(self):
        self.galaxy.is_active = False
        self.galaxy.save()
        response = self.client.get(reverse("products:home"))
        self.assertNotContains(response, "Galaxy S26")

    def test_out_of_stock_badge(self):
        response = self.client.get(reverse("products:home"))
        self.assertContains(response, "Rupture de stock")

    def test_detail_page(self):
        response = self.client.get(reverse("products:detail", args=[self.galaxy.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Un super téléphone")

    def test_detail_404_for_unknown_product(self):
        response = self.client.get(reverse("products:detail", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_detail_404_for_inactive_product(self):
        self.galaxy.is_active = False
        self.galaxy.save()
        response = self.client.get(reverse("products:detail", args=[self.galaxy.pk]))
        self.assertEqual(response.status_code, 404)


class SearchAndFilterTests(BaseTestCase):
    def search(self, **params):
        return self.client.get(reverse("products:home"), params)

    def test_search_by_keyword(self):
        response = self.search(q="robe")
        self.assertContains(response, "Robe rouge")
        self.assertNotContains(response, "Galaxy S26")

    def test_search_in_description(self):
        response = self.search(q="téléphone")
        self.assertContains(response, "Galaxy S26")

    def test_filter_by_category(self):
        response = self.search(category=self.phones.pk)
        self.assertContains(response, "Galaxy S26")
        self.assertNotContains(response, "Robe rouge")

    def test_filter_by_price_range(self):
        response = self.search(min_price="100", max_price="1000")
        self.assertContains(response, "Galaxy S26")
        self.assertNotContains(response, "Robe rouge")

    def test_combined_filters(self):
        response = self.search(category=self.phones.pk, max_price="100")
        self.assertNotContains(response, "Galaxy S26")

    def test_no_result_message(self):
        response = self.search(q="zzzzzz")
        self.assertContains(response, "Aucun produit ne correspond")


# ---------- ESPACE VENDEUR ET PERMISSIONS ----------

class SellerTests(BaseTestCase):
    def product_data(self, **overrides):
        data = {
            "category": self.phones.pk, "name": "iPhone 18", "description": "Nouveau",
            "price": "1500", "stock": "2", "is_active": "on",
        }
        data.update(overrides)
        return data

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse("products:my_products"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_client_cannot_access_seller_pages(self):
        self.login("client1")
        response = self.client.get(reverse("products:my_products"))
        self.assertEqual(response.status_code, 302)

    def test_pending_seller_cannot_access(self):
        self.login("pending")
        response = self.client.get(reverse("products:create"))
        self.assertEqual(response.status_code, 302)

    def test_seller_sees_only_own_products(self):
        self.login("seller1")
        response = self.client.get(reverse("products:my_products"))
        self.assertContains(response, "Galaxy S26")
        self.assertNotContains(response, "Robe rouge")

    def test_seller_can_create_product_with_image(self):
        self.login("seller1")
        response = self.client.post(
            reverse("products:create"), self.product_data(image=make_image())
        )
        self.assertRedirects(response, reverse("products:my_products"))
        product = Product.objects.get(name="iPhone 18")
        self.assertEqual(product.store, self.store1)  # store attaché automatiquement
        self.assertTrue(product.image.name.startswith("products/"))
        product.image.delete()  # nettoie le fichier de test

    def test_invalid_product_is_not_saved(self):
        self.login("seller1")
        count = Product.objects.count()
        response = self.client.post(reverse("products:create"), self.product_data(price="-1"))
        self.assertEqual(response.status_code, 200)  # le formulaire est réaffiché
        self.assertEqual(Product.objects.count(), count)

    def test_seller_can_edit_own_product(self):
        self.login("seller1")
        self.client.post(
            reverse("products:update", args=[self.galaxy.pk]),
            self.product_data(name="Galaxy S26 Ultra", price="950"),
        )
        self.galaxy.refresh_from_db()
        self.assertEqual(self.galaxy.name, "Galaxy S26 Ultra")

    def test_seller_cannot_edit_other_sellers_product(self):
        self.login("seller1")
        response = self.client.get(reverse("products:update", args=[self.dress.pk]))
        self.assertEqual(response.status_code, 404)

    def test_seller_cannot_delete_other_sellers_product(self):
        self.login("seller1")
        response = self.client.post(reverse("products:delete", args=[self.dress.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Product.objects.filter(pk=self.dress.pk).exists())

    def test_seller_can_delete_own_product(self):
        self.login("seller1")
        self.client.post(reverse("products:delete", args=[self.galaxy.pk]))
        self.assertFalse(Product.objects.filter(pk=self.galaxy.pk).exists())

    def test_delete_requires_confirmation(self):
        self.login("seller1")
        self.client.get(reverse("products:delete", args=[self.galaxy.pk]))
        self.assertTrue(Product.objects.filter(pk=self.galaxy.pk).exists())


# ---------- FAVORIS ----------

class FavoriteTests(BaseTestCase):
    def toggle(self):
        return self.client.post(reverse("products:favorite_toggle", args=[self.galaxy.pk]))

    def test_client_can_add_and_remove_favorite(self):
        self.login("client1")
        self.toggle()
        self.assertEqual(Favorite.objects.count(), 1)
        self.toggle()
        self.assertEqual(Favorite.objects.count(), 0)

    def test_favorites_page_lists_products(self):
        self.login("client1")
        self.toggle()
        response = self.client.get(reverse("products:favorites"))
        self.assertContains(response, "Galaxy S26")

    def test_anonymous_cannot_favorite(self):
        response = self.toggle()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Favorite.objects.count(), 0)

    def test_seller_cannot_favorite(self):
        self.login("seller1")
        self.toggle()
        self.assertEqual(Favorite.objects.count(), 0)

    def test_toggle_refuses_get_requests(self):
        self.login("client1")
        response = self.client.get(reverse("products:favorite_toggle", args=[self.galaxy.pk]))
        self.assertEqual(response.status_code, 405)

    def test_unsafe_redirect_is_ignored(self):
        self.login("client1")
        response = self.client.post(
            reverse("products:favorite_toggle", args=[self.galaxy.pk]),
            {"next": "https://evil.example.com"},
        )
        self.assertEqual(response.url, reverse("products:detail", args=[self.galaxy.pk]))


# ---------- AVIS ----------

class ReviewTests(BaseTestCase):
    def post_review(self, rating, comment="ok"):
        return self.client.post(
            reverse("products:detail", args=[self.galaxy.pk]),
            {"rating": rating, "comment": comment},
        )

    def test_client_can_post_review(self):
        self.login("client1")
        self.post_review(5, "Super")
        self.assertEqual(Review.objects.count(), 1)

    def test_posting_again_updates_review(self):
        self.login("client1")
        self.post_review(5)
        self.post_review(2, "Finalement moyen")
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(Review.objects.get().rating, 2)

    def test_invalid_rating_is_rejected(self):
        self.login("client1")
        self.post_review(9)
        self.assertEqual(Review.objects.count(), 0)

    def test_seller_cannot_review(self):
        self.login("seller1")
        self.post_review(5)
        self.assertEqual(Review.objects.count(), 0)

    def test_anonymous_cannot_review(self):
        self.post_review(5)
        self.assertEqual(Review.objects.count(), 0)

    def test_average_rating_is_displayed(self):
        other = User.objects.create_user("client2", "c2@test.com", "pass12345")
        Review.objects.create(user=self.client_user, product=self.galaxy, rating=5)
        Review.objects.create(user=other, product=self.galaxy, rating=3)
        response = self.client.get(reverse("products:detail", args=[self.galaxy.pk]))
        self.assertContains(response, "4.0")
        self.assertContains(response, "2 avis")

    def test_client_can_delete_own_review(self):
        review = Review.objects.create(user=self.client_user, product=self.galaxy, rating=4)
        self.login("client1")
        self.client.post(reverse("products:review_delete", args=[review.pk]))
        self.assertEqual(Review.objects.count(), 0)

    def test_client_cannot_delete_someone_elses_review(self):
        other = User.objects.create_user("client2", "c2@test.com", "pass12345")
        review = Review.objects.create(user=other, product=self.galaxy, rating=4)
        self.login("client1")
        response = self.client.post(reverse("products:review_delete", args=[review.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Review.objects.count(), 1)