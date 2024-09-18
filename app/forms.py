from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model  # Usar get_user_model para obtener el modelo de usuario personalizado

CustomUser = get_user_model()  # Obtiene el modelo de usuario personalizado

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser  # Usar CustomUser en lugar de User
        fields = ['username', "first_name", "last_name", "email", "password1", "password2"]
