from rest_framework.permissions import BasePermission


class IsAdminOrCreateOnly(BasePermission):
    message = "You must be an admin to view this list"

    def has_permission(self, request, view):
        return request.method in ["POST"] or request.user.is_staff


class IsOwnerOrAdmin(BasePermission):
    message = (
        "You must be the owner of this instance or an admin to perform this action."  # noqa
    )

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


class IsOwnerOrAdminOrReadOnly(BasePermission):
    message = (
        "You must be the owner of this instance or an admin to modify this content. "  # noqa
        "Read-only access is allowed for everyone."
    )

    def has_object_permission(self, request, view, obj):
        return request.method in ["GET", "HEAD", "OPTIONS"] or (
            request.user.is_staff or obj.user == request.user
        )


class IsAdminOrReadOnly(BasePermission):
    message = "You must be an admin to modify this content. Read-only access is allowed for everyone."  # noqa

    def has_permission(self, request, view):
        return request.method in ["GET", "HEAD", "OPTIONS"] or request.user.is_staff  # noqa
