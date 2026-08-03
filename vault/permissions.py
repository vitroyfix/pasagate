from rest_framework import permissions


class IsMerchantOwner(permissions.BasePermission):
    """
    Object-level check: a user may only read/write Merchant records they own.
    Without this, ANY logged-in user could hit /merchants/<id>/ for ANY id,
    not just their own — plain IsAuthenticated alone doesn't stop that.
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner_id == request.user.id