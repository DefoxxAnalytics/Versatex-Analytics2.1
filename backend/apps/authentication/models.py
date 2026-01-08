"""
Authentication models for organization-based multi-tenancy
"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError


class Organization(models.Model):
    """
    Organization model for multi-tenancy
    Each organization has its own isolated data
    """
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Branding fields for reports
    logo = models.ImageField(
        upload_to='org_logos/',
        null=True,
        blank=True,
        help_text='Organization logo for reports (recommended: 200x60px PNG)'
    )
    primary_color = models.CharField(
        max_length=7,
        default='#1e3a5f',
        help_text='Primary brand color in hex format (e.g., #1e3a5f)'
    )
    secondary_color = models.CharField(
        max_length=7,
        default='#2563eb',
        help_text='Secondary brand color in hex format (e.g., #2563eb)'
    )
    report_footer = models.TextField(
        blank=True,
        default='',
        help_text='Custom footer text for reports (e.g., confidentiality notice)'
    )
    website = models.URLField(
        blank=True,
        help_text='Organization website URL'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self):
        return self.name

    def get_branding(self):
        """Return branding configuration for reports."""
        return {
            'name': self.name,
            'logo_path': self.logo.path if self.logo else None,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'footer': self.report_footer,
            'website': self.website,
        }


class UserProfile(models.Model):
    """
    Extended user profile with organization and role
    """
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('viewer', 'Viewer'),
    ]

    # Allowed keys for the preferences JSONField
    ALLOWED_PREFERENCE_KEYS = {
        'theme', 'colorScheme', 'notifications', 'exportFormat',
        'currency', 'dateFormat', 'dashboardLayout', 'sidebarCollapsed'
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='users'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    preferences = models.JSONField(default=dict, blank=True, help_text='User preferences (theme, notifications, etc.)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__username']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.role})"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_manager(self):
        return self.role in ['admin', 'manager']
    
    def can_upload_data(self):
        return self.role in ['admin', 'manager']
    
    def can_delete_data(self):
        return self.role == 'admin'

    def is_super_admin(self):
        """Check if user is a super admin (Django superuser).

        Super admins have platform-level privileges that transcend organization
        boundaries, such as uploading data for multiple organizations at once.
        """
        return self.user.is_superuser


class AuditLog(models.Model):
    """
    Audit log for tracking user actions.

    Security: The details JSONField is validated to only accept known keys
    to prevent injection of arbitrary data.
    """
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('upload', 'Upload'),
        ('export', 'Export'),
        ('download', 'Download'),  # Report downloads
        ('view', 'View'),
        ('reset', 'Reset'),           # Organization reset
        ('bulk_delete', 'Bulk Delete'),  # Delete all data
        ('generate', 'Generate'),  # Report generation
    ]

    # Allowed keys for the details JSONField (security: prevent arbitrary data injection)
    ALLOWED_DETAIL_KEYS = {
        'file_name', 'successful', 'failed', 'duplicate', 'batch_id', 'record_id',
        'changes', 'count', 'username', 'error', 'old_value', 'new_value',
        'reason', 'target_id', 'target_type', 'organizations_affected',
        # Organization switcher (superuser feature)
        'organization_id',
        # AI & Predictive Analytics keys
        'months', 'category_id', 'supplier_id', 'annual_budget', 'days',
        'contract_id', 'violation_id', 'resolved', 'severity', 'sensitivity',
        'insight_count', 'resolution_notes',
        # Tail Spend Analysis keys
        'threshold',
        # Data Upload Center keys
        'organization_name', 'deleted_counts', 'transactions_deleted', 'uploads_deleted',
        'suppliers_deleted', 'categories_deleted', 'templates_deleted', 'contracts_deleted',
        'duplicates', 'skipped', 'template_name', 'mapping_snapshot', 'processing_mode',
        # Reports module keys
        'report_type', 'report_id', 'schedule_id', 'format', 'async', 'name',
        # P2P Analytics keys
        'weeks', 'stage', 'invoice_id', 'pr_id', 'po_id', 'limit',
        'status', 'exception_type', 'resolved_count', 'failed_count'
    }

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['organization', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]

    def clean(self):
        """Validate audit log details schema."""
        super().clean()
        if self.details:
            if not isinstance(self.details, dict):
                raise ValidationError({'details': 'Details must be a dictionary'})

            invalid_keys = set(self.details.keys()) - self.ALLOWED_DETAIL_KEYS
            if invalid_keys:
                raise ValidationError({
                    'details': f"Invalid audit log detail keys: {', '.join(sorted(invalid_keys))}"
                })

            # Validate value types (simple types only for security)
            for key, value in self.details.items():
                if value is not None and not isinstance(value, (str, int, float, bool, list)):
                    raise ValidationError({
                        'details': f"Invalid value type for key '{key}'. Only str, int, float, bool, list allowed."
                    })

    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.resource} at {self.timestamp}"


# Signal to create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create UserProfile when User is created
    Note: Organization must be set manually after creation
    """
    if created and not hasattr(instance, 'profile'):
        # Don't auto-create profile, let registration handle it
        pass
