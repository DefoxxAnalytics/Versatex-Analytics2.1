"""
Procurement data models with security enhancements:
- UUID fields for IDOR protection
- Encrypted fields for sensitive data
- Secure file name handling
"""
import uuid
import re
from django.db import models
from django.contrib.auth.models import User
from apps.authentication.models import Organization

# Note: Field encryption is optional. To enable it:
# 1. Set FIELD_ENCRYPTION_KEY in your environment
# 2. Install django-encrypted-model-fields
# When not configured, standard Django fields are used instead.
# For now, we use regular fields for maximum compatibility.


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal attacks.
    Removes directory components and special characters.
    """
    if not filename:
        return 'unnamed_file'

    # Remove any directory components
    filename = filename.replace('\\', '/').split('/')[-1]

    # Remove any path traversal attempts
    filename = re.sub(r'\.\.+', '', filename)

    # Remove any null bytes
    filename = filename.replace('\x00', '')

    # Keep only safe characters
    safe_filename = re.sub(r'[^\w\s\-\.]', '', filename)

    # Ensure filename is not empty and doesn't start with a dot
    if not safe_filename or safe_filename.startswith('.'):
        safe_filename = 'file_' + safe_filename

    # Limit length
    if len(safe_filename) > 200:
        name, ext = safe_filename.rsplit('.', 1) if '.' in safe_filename else (safe_filename, '')
        safe_filename = name[:195] + ('.' + ext if ext else '')

    return safe_filename


class Supplier(models.Model):
    """
    Supplier model - organization-scoped
    Includes UUID for secure external references
    """
    # UUID for external API references (prevents ID enumeration)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='suppliers'
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, blank=True)

    # Contact information (consider enabling field encryption in production)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['organization', 'name']
        indexes = [
            models.Index(fields=['organization', 'name']),
            models.Index(fields=['uuid']),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Category(models.Model):
    """
    Category model - organization-scoped
    Includes UUID for secure external references
    """
    # UUID for external API references
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='subcategories'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'
        unique_together = ['organization', 'name']
        indexes = [
            models.Index(fields=['organization', 'name']),
            models.Index(fields=['uuid']),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Transaction(models.Model):
    """
    Procurement transaction model - organization-scoped
    Includes UUID for secure external references
    """
    # UUID for external API references
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_transactions'
    )

    # Core fields
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='transactions'
    )

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)

    # Optional fields
    subcategory = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    fiscal_year = models.IntegerField(null=True, blank=True)
    spend_band = models.CharField(max_length=50, blank=True)
    payment_method = models.CharField(max_length=100, blank=True)

    # Invoice number (consider enabling field encryption in production)
    invoice_number = models.CharField(max_length=100, blank=True)

    # Metadata
    upload_batch = models.CharField(max_length=100, blank=True)  # For tracking uploads
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['organization', '-date']),
            models.Index(fields=['organization', 'supplier']),
            models.Index(fields=['organization', 'category']),
            models.Index(fields=['organization', 'fiscal_year']),
            models.Index(fields=['upload_batch']),
            models.Index(fields=['uuid']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'supplier', 'category', 'amount', 'date', 'invoice_number'],
                name='unique_transaction_with_invoice'
            ),
        ]

    def __str__(self):
        return f"{self.supplier.name} - {self.amount} on {self.date}"


class ColumnMappingTemplate(models.Model):
    """
    Stores reusable column mapping configurations for CSV uploads.
    Scoped per-organization to allow different teams to have their own templates.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='mapping_templates'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    mapping = models.JSONField(default=dict)  # {"csv_column": "target_field"}
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_mapping_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']
        unique_together = ['organization', 'name']
        verbose_name = 'Column Mapping Template'
        verbose_name_plural = 'Column Mapping Templates'
        indexes = [
            models.Index(fields=['organization', 'is_default']),
            models.Index(fields=['uuid']),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

    def save(self, *args, **kwargs):
        # Ensure only one default per organization
        if self.is_default:
            ColumnMappingTemplate.objects.filter(
                organization=self.organization,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class DataUpload(models.Model):
    """
    Track data upload history with background processing support.
    Includes UUID for secure external references.
    """
    # UUID for external API references
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='data_uploads'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='data_uploads'
    )

    # Sanitized file name - original name stored separately
    file_name = models.CharField(max_length=255)
    original_file_name = models.CharField(max_length=255, blank=True)
    file_size = models.IntegerField()  # in bytes
    batch_id = models.CharField(max_length=100, unique=True)

    # Statistics
    total_rows = models.IntegerField(default=0)
    successful_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    duplicate_rows = models.IntegerField(default=0)

    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partially Completed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    error_log = models.JSONField(default=list, blank=True)

    # Background processing support
    celery_task_id = models.CharField(max_length=255, blank=True, db_index=True)
    progress_percent = models.IntegerField(default=0)
    progress_message = models.CharField(max_length=255, blank=True)

    # Column mapping tracking
    column_mapping_template = models.ForeignKey(
        'ColumnMappingTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploads'
    )
    column_mapping_snapshot = models.JSONField(default=dict, blank=True)

    # File storage for async processing
    stored_file = models.FileField(
        upload_to='uploads/%Y/%m/%d/',
        null=True,
        blank=True
    )

    # Processing mode indicator
    PROCESSING_MODE_CHOICES = [
        ('sync', 'Synchronous'),
        ('async', 'Asynchronous'),
    ]
    processing_mode = models.CharField(
        max_length=10,
        choices=PROCESSING_MODE_CHOICES,
        default='sync'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['batch_id']),
            models.Index(fields=['uuid']),
            models.Index(fields=['celery_task_id']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        # Sanitize file name before saving
        if self.file_name and not self.original_file_name:
            self.original_file_name = self.file_name
        self.file_name = sanitize_filename(self.file_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.file_name} - {self.status} ({self.organization.name})"


class Contract(models.Model):
    """
    Contract model for tracking supplier agreements.
    Contracts are imported via CSV (read-only in frontend).
    Used for contract analytics and compliance tracking.
    """
    # UUID for external API references
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='contracts'
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='contracts'
    )

    # Contract Details
    contract_number = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Financial Terms
    total_value = models.DecimalField(max_digits=15, decimal_places=2)
    annual_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # Dates
    start_date = models.DateField()
    end_date = models.DateField()
    renewal_notice_days = models.IntegerField(default=90)

    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expiring', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('renewed', 'Renewed'),
        ('terminated', 'Terminated'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    auto_renew = models.BooleanField(default=False)

    # Categories covered by this contract
    categories = models.ManyToManyField(Category, blank=True, related_name='contracts')

    # Import tracking
    upload_batch = models.CharField(max_length=100, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['end_date']
        unique_together = ['organization', 'contract_number']
        indexes = [
            models.Index(fields=['organization', 'end_date']),
            models.Index(fields=['organization', 'supplier']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['uuid']),
        ]

    def __str__(self):
        return f"{self.contract_number} - {self.title} ({self.supplier.name})"

    @property
    def days_to_expiry(self):
        """Calculate days until contract expires."""
        from datetime import date
        if self.end_date:
            return (self.end_date - date.today()).days
        return None

    @property
    def is_expiring_soon(self):
        """Check if contract is expiring within renewal notice period."""
        days = self.days_to_expiry
        return days is not None and 0 < days <= self.renewal_notice_days


class SpendingPolicy(models.Model):
    """
    Spending policy model for compliance tracking.
    Defines rules for maverick spend detection.
    """
    # UUID for external API references
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='spending_policies'
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Policy Rules (JSON for flexibility)
    # Example structure:
    # {
    #     "max_transaction_amount": 10000,
    #     "required_approval_threshold": 5000,
    #     "preferred_suppliers": ["uuid1", "uuid2"],
    #     "restricted_categories": ["uuid3"],
    #     "require_contract": true
    # }
    rules = models.JSONField(default=dict)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Spending policies'
        unique_together = ['organization', 'name']
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['uuid']),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class PolicyViolation(models.Model):
    """
    Policy violation model for tracking compliance issues.
    Records transactions that violate spending policies.
    """
    # UUID for external API references
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='policy_violations'
    )
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='violations'
    )
    policy = models.ForeignKey(
        SpendingPolicy,
        on_delete=models.CASCADE,
        related_name='violations'
    )

    # Violation Details
    VIOLATION_TYPE_CHOICES = [
        ('amount_exceeded', 'Amount Exceeded'),
        ('non_preferred_supplier', 'Non-Preferred Supplier'),
        ('restricted_category', 'Restricted Category'),
        ('no_contract', 'No Contract Coverage'),
        ('approval_missing', 'Approval Missing'),
    ]
    violation_type = models.CharField(max_length=50, choices=VIOLATION_TYPE_CHOICES)

    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')

    # Additional details about the violation
    details = models.JSONField(default=dict)

    # Resolution tracking
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='resolved_violations'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['organization', 'is_resolved']),
            models.Index(fields=['organization', 'severity']),
            models.Index(fields=['uuid']),
        ]

    def __str__(self):
        return f"{self.violation_type} - {self.transaction} ({self.severity})"
