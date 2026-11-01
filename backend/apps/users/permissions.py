from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    """本人或管理员可访问"""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == 'admin' or request.user.is_superuser or request.user.is_staff:
            return True
        return obj == request.user


def IsRole(role_name):
    """工厂函数：要求用户角色匹配指定 role_name（或管理员放行）"""

    class _IsRole(BasePermission):
        def has_permission(self, request, view):
            if not (request.user and request.user.is_authenticated):
                return False
            if request.user.role == 'admin' or request.user.is_superuser or request.user.is_staff:
                return True
            return request.user.role == role_name

    return _IsRole
