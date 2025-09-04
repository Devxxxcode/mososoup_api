from rest_framework.permissions import BasePermission,SAFE_METHODS

class IsSiteAdmin(BasePermission):
    """
    Custom permission to allow access only to site administrators.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated and has the 'is_staff' attribute set to True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
    

from rest_framework.permissions import BasePermission


class IsAdminOrReadCreateOnlyForRegularUsers(BasePermission):
    """
    Custom permission:
    - Admin users have full access.
    - Regular users can only read (GET) and create (POST) their own deposits.
    """
    def has_permission(self, request, view):
        # Admin users have full access
        if request.user.is_staff:
            return True
        # Regular users can only perform safe methods (GET, POST)
        return view.action in ['list', 'retrieve', 'create']

    def has_object_permission(self, request, view, obj):
        # Admin users have full access to objects
        if request.user.is_staff:
            return True
        # Regular users can only access their own deposits
        return obj.user == request.user
    
class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to allow only admin users to modify objects.
    Read-only access is allowed for all other users.
    """

    def has_permission(self, request, view):
        # Allow read-only access for safe methods (GET, HEAD, OPTIONS)
        if request.method in SAFE_METHODS:
            return True

        # Allow full access only for admin users
        return request.user and request.user.is_staff

