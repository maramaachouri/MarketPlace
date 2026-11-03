
from django import forms

from .models import Store


class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ["name", "description", "logo", "address"]

        labels = {
            "name": "Nom de la boutique",
            "description": "Description",
            "logo": "Logo de la boutique",
            "address": "Adresse",
        }

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex. : Maram Fashion",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Présentez votre boutique...",
                "rows": 4,
            }),
            "logo": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
            }),
            "address": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Adresse de la boutique",
            }),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        if not name:
            raise forms.ValidationError(
                "Le nom de la boutique est obligatoire."
            )

        return name
