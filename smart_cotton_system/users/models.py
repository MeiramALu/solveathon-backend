# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Роли согласно вашему проекту
    ROLE_CHOICES = (
        ('FARMER', 'Фермер'),      # Доступ к модулю полива и семян
        ('LAB', 'Лаборант'),       # Ввод данных HVI
        ('FACTORY', 'Завод'),      # Управление производством
        ('LOGISTICS', 'Логист'),   # Транспорт
        ('ADMIN', 'Администратор'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='FARMER')
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"