
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "exemple@email.com",
        }),
    )

    first_name = forms.CharField(
        required=True,
        label="Prénom",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Votre prénom",
        }),
    )

    last_name = forms.CharField(
        required=True,
        label="Nom",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Votre nom",
        }),
    )

    
    role = forms.ChoiceField(
        choices=[
            (User.Role.CLIENT, "Client"),
            (User.Role.SELLER, "Vendeur"),
        ],
        initial=User.Role.CLIENT,
        label="Type de compte",
        widget=forms.Select(attrs={
            "class": "form-select",
        }),
    )


    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if field_name in ("password1", "password2"):
                field.widget.attrs.update({
                    "class": "form-control",
                    "placeholder": "••••••••",
                })
            elif field_name == "username":
                field.widget.attrs.update({
                    "class": "form-control",
                    "placeholder": "Choisissez un nom d'utilisateur",
                })

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Cette adresse e-mail est déjà utilisée."
            )

        return email

    def clean_role(self):
        role = self.cleaned_data["role"]

        if role not in [User.Role.CLIENT, User.Role.SELLER]:
            raise forms.ValidationError(
                "Ce type de compte n'est pas autorisé."
            )

        return role

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Votre nom d'utilisateur",
        }),
    )

    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Votre mot de passe",
        }),
    )

class ProfileUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

        labels = {
            "first_name": "Prénom",
            "last_name": "Nom",
            "email": "Adresse e-mail",
        }

        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Votre prénom",
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Votre nom",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "exemple@email.com",
            }),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError(
                "Cette adresse e-mail est déjà utilisée."
            )

        return email
