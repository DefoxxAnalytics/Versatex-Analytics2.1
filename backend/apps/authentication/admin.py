"""
Django admin configuration for authentication
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Organization, UserProfile, AuditLog, UserOrganizationMembership


class UserOrganizationMembershipInline(admin.TabularInline):
    """Inline admin for managing user memberships from User admin."""
    model = UserOrganizationMembership
    fk_name = 'user'
    extra = 0
    fields = ['organization', 'role', 'is_primary', 'is_active', 'created_at']
    readonly_fields = ['created_at']
    autocomplete_fields = ['organization']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'profile'):
            # Org admins can only see memberships in their organizations
            admin_org_ids = UserOrganizationMembership.objects.filter(
                user=request.user,
                role='admin',
                is_active=True
            ).values_list('organization_id', flat=True)
            return qs.filter(organization_id__in=admin_org_ids)
        return qs.none()


class UserProfileInline(admin.StackedInline):
    """Inline for UserProfile on User admin."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['organization', 'role', 'phone', 'department', 'is_active']


# Unregister the default User admin and re-register with inlines
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Extended User admin with profile and memberships inlines."""
    inlines = [UserProfileInline, UserOrganizationMembershipInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'get_organization', 'get_membership_count']

    def get_organization(self, obj):
        """Get user's primary organization."""
        if hasattr(obj, 'profile'):
            return obj.profile.organization.name if obj.profile.organization else '-'
        return '-'
    get_organization.short_description = 'Organization'

    def get_membership_count(self, obj):
        """Get count of organizations user belongs to."""
        return UserOrganizationMembership.objects.filter(user=obj, is_active=True).count()
    get_membership_count.short_description = 'Orgs'


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'member_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']

    def member_count(self, obj):
        """Return count of active members in this organization."""
        return obj.user_memberships.filter(is_active=True).count()
    member_count.short_description = 'Members'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'role', 'membership_count', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'organization', 'created_at']
    search_fields = ['user__username', 'user__email', 'organization__name']
    readonly_fields = ['created_at', 'updated_at']

    def membership_count(self, obj):
        """Return count of organizations this user belongs to."""
        return UserOrganizationMembership.objects.filter(
            user=obj.user,
            is_active=True
        ).count()
    membership_count.short_description = 'Orgs'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'profile'):
            return qs.filter(organization=request.user.profile.organization)
        return qs.none()


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'action', 'resource', 'timestamp']
    list_filter = ['action', 'organization', 'timestamp']
    search_fields = ['user__username', 'resource', 'resource_id']
    readonly_fields = ['user', 'organization', 'action', 'resource', 'resource_id',
                      'details', 'ip_address', 'user_agent', 'timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'profile'):
            return qs.filter(organization=request.user.profile.organization)
        return qs.none()


@admin.register(UserOrganizationMembership)
class UserOrganizationMembershipAdmin(admin.ModelAdmin):
    """Admin for managing organization memberships directly."""
    list_display = ['user', 'organization', 'role', 'is_primary', 'is_active', 'created_at']
    list_filter = ['role', 'is_primary', 'is_active', 'organization', 'created_at']
    search_fields = ['user__username', 'user__email', 'organization__name']
    autocomplete_fields = ['user', 'organization']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['invited_by']
    list_editable = ['role', 'is_primary', 'is_active']

    fieldsets = (
        (None, {
            'fields': ('user', 'organization', 'role')
        }),
        ('Status', {
            'fields': ('is_primary', 'is_active')
        }),
        ('Metadata', {
            'fields': ('invited_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user', 'organization', 'invited_by')
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'profile'):
            # Org admins can only see memberships in orgs they manage
            admin_org_ids = UserOrganizationMembership.objects.filter(
                user=request.user,
                role='admin',
                is_active=True
            ).values_list('organization_id', flat=True)
            return qs.filter(organization_id__in=admin_org_ids)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit organization choices for non-superusers."""
        if db_field.name == 'organization' and not request.user.is_superuser:
            if hasattr(request.user, 'profile'):
                admin_org_ids = UserOrganizationMembership.objects.filter(
                    user=request.user,
                    role='admin',
                    is_active=True
                ).values_list('organization_id', flat=True)
                kwargs['queryset'] = Organization.objects.filter(id__in=admin_org_ids)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
