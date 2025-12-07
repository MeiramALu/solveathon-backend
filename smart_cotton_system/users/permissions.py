# users/permissions.py
from rest_framework import permissions

class IsFarmer(permissions.BasePermission):
    """
    Разрешает доступ только пользователям с ролью FARMER.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'FARMER')

class IsLabOrReadOnly(permissions.BasePermission):
    """
    Разрешает менять данные только Лаборантам (LAB).
    Остальные могут только смотреть (безопасные методы GET).
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.role == 'LAB')