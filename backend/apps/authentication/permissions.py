"""
Custom permissions for role-based access control
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission class for admin-only access
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.is_admin()
        )


class IsManager(permissions.BasePermission):
    """
    Permission class for manager and admin access
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.is_manager()
        )


class CanUploadData(permissions.BasePermission):
    """
    Permission class for users who can upload data
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.can_upload_data()
        )


class CanDeleteData(permissions.BasePermission):
    """
    Permission class for users who can delete data
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.can_delete_data()
        )


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission class for super admin (Django superuser) access.

    Super admins have platform-level privileges that transcend organization
    boundaries, such as uploading data for multiple organizations at once.
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser
        )


class IsSameOrganization(permissions.BasePermission):
    """
    Permission class to ensure users can only access their organization's data.

    Super admins (Django superusers) bypass this check and can access data
    from any organization.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Super admins can access any organization's data
        if request.user.is_superuser:
            return True

        if not hasattr(request.user, 'profile'):
            return False

        # Check if object has organization field
        if hasattr(obj, 'organization'):
            return obj.organization == request.user.profile.organization

        # Check if object has user field with profile
        if hasattr(obj, 'user') and hasattr(obj.user, 'profile'):
            return obj.user.profile.organization == request.user.profile.organization

        return False


# =============================================================================
# P2P (Procure-to-Pay) Permissions
# =============================================================================

class HasP2PAccess(permissions.BasePermission):
    """
    Check if user has access to P2P Analytics module.
    All authenticated users with a profile can access P2P data by default.
    Can be extended to check organization-level feature flags.
    """
    message = 'P2P Analytics module access required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers always have access
        if request.user.is_superuser:
            return True

        if not hasattr(request.user, 'profile'):
            return False

        # Check organization-level P2P module flag if it exists
        # (can be added to Organization model later)
        org = request.user.profile.organization
        if hasattr(org, 'p2p_module_enabled'):
            return org.p2p_module_enabled

        # Default: all users can access P2P if they have a profile
        return request.user.profile.is_active


class CanResolveExceptions(permissions.BasePermission):
    """
    Only managers and admins can resolve invoice exceptions.
    This is a write operation that affects financial data.
    """
    message = 'Only managers and admins can resolve invoice exceptions.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        if not hasattr(request.user, 'profile'):
            return False

        return request.user.profile.role in ['admin', 'manager']


class CanViewPaymentData(permissions.BasePermission):
    """
    Only managers and admins can view sensitive payment data.
    This includes supplier payment performance and cash flow forecasts.
    """
    message = 'Only managers and admins can view payment data.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        if not hasattr(request.user, 'profile'):
            return False

        return request.user.profile.role in ['admin', 'manager']


class CanApprovePO(permissions.BasePermission):
    """
    Only managers and admins can approve purchase orders.
    This is a critical workflow action.
    """
    message = 'Only managers and admins can approve purchase orders.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        if not hasattr(request.user, 'profile'):
            return False

        return request.user.profile.role in ['admin', 'manager']


class CanApprovePR(permissions.BasePermission):
    """
    Only managers and admins can approve purchase requisitions.
    This is a critical workflow action.
    """
    message = 'Only managers and admins can approve purchase requisitions.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        if not hasattr(request.user, 'profile'):
            return False

        return request.user.profile.role in ['admin', 'manager']


class CanViewOwnRequisitions(permissions.BasePermission):
    """
    Viewers can only see their own requisitions.
    Managers and admins can see all requisitions in their organization.
    """
    message = 'You can only view your own requisitions.'

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        if not hasattr(request.user, 'profile'):
            return False

        user_org = request.user.profile.organization

        # Check organization match first
        if obj.organization != user_org:
            return False

        # Managers and admins can see all org PRs
        if request.user.profile.role in ['admin', 'manager']:
            return True

        # Viewers can only see their own PRs
        return obj.requested_by == request.user
