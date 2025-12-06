from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


# Создаем настройки админки для нашего кастомного юзера
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Какие колонки показывать в списке пользователей
    list_display = ('username', 'email', 'role', 'is_staff')

    # Фильтры справа (по роли и статусу)
    list_filter = ('role', 'is_staff', 'is_active')

    # По каким полям искать
    search_fields = ('username', 'email')

    # Это нужно, чтобы поле 'role' появилось в форме редактирования пользователя
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация (Роль)', {'fields': ('role',)}),
    )

    # Это нужно, чтобы поле 'role' было при создании нового пользователя
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация (Роль)', {'fields': ('role',)}),
    )