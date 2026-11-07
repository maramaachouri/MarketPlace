from django import forms

from .models import Category, Product, Review


class ProductForm(forms.ModelForm):
    """Formulaire utilisé par le vendeur pour ajouter / modifier un produit."""

    class Meta:
        model = Product
        fields = ["category", "name", "description", "price", "stock", "image", "is_active"]

        labels = {
            "category": "Catégorie",
            "name": "Nom du produit",
            "description": "Description",
            "price": "Prix (DT)",
            "stock": "Quantité en stock",
            "image": "Image du produit",
            "is_active": "Produit visible dans le catalogue",
        }

        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex. : iPhone 15"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 3:
            raise forms.ValidationError("Le nom doit contenir au moins 3 caractères.")
        return name

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Le prix doit être supérieur à 0.")
        return price


class ProductFilterForm(forms.Form):
    """Formulaire de recherche et de filtres."""

    q = forms.CharField(
        required=False,
        label="Recherche",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Rechercher un produit..."}),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Toutes les catégories",
        label="Catégorie",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        label="Prix min",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Prix min", "min": "0"}),
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        label="Prix max",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Prix max", "min": "0"}),
    )

    def clean(self):
        cleaned = super().clean()
        min_price = cleaned.get("min_price")
        max_price = cleaned.get("max_price")
        if min_price is not None and max_price is not None and min_price > max_price:
            raise forms.ValidationError("Le prix min ne peut pas dépasser le prix max.")
        return cleaned


class ReviewForm(forms.ModelForm):
    """Formulaire d'avis : note de 1 à 5 + commentaire."""

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        labels = {"rating": "Votre note", "comment": "Votre commentaire"}
        widgets = {
            "rating": forms.Select(attrs={"class": "form-select"}),
            "comment": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Partagez votre expérience (facultatif)",
            }),
        }