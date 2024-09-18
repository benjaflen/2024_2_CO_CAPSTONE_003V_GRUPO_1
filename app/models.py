from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_conductor = models.BooleanField(default=False)
    is_apoderado = models.BooleanField(default=False)
