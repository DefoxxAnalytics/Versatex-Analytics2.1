"""
Django Admin configuration for the reports module.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Admin interface for Report model."""

    list_display = [
        'name', 'report_type', 'report_format', 'status_badge',
        'organization', 'created_by', 'created_at', 'generated_at'
    ]
    list_filter = [
        'status', 'report_type', 'report_format', 'organization',
        'is_scheduled', 'created_at'
    ]
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'generated_at',
        'file_size', 'summary_data_preview'
    ]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'report_type', 'report_format')
        }),
        ('Organization & Ownership', {
            'fields': ('organization', 'created_by')
        }),
        ('Date Range', {
            'fields': ('period_start', 'period_end')
        }),
        ('Filters & Parameters', {
            'fields': ('filters', 'parameters'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'error_message', 'file_path', 'file_size')
        }),
        ('Generated Data', {
            'fields': ('summary_data_preview',),
            'classes': ('collapse',)
        }),
        ('Sharing', {
            'fields': ('is_public', 'shared_with')
        }),
        ('Scheduling', {
            'fields': ('is_scheduled', 'schedule_frequency', 'next_run', 'last_run')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'generated_at')
        }),
    )

    filter_horizontal = ['shared_with']

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'draft': '#6b7280',      # gray
            'generating': '#f59e0b',  # amber
            'completed': '#10b981',   # green
            'failed': '#ef4444',      # red
            'scheduled': '#3b82f6',   # blue
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def summary_data_preview(self, obj):
        """Show truncated preview of summary_data."""
        if not obj.summary_data:
            return "No data"
        import json
        preview = json.dumps(obj.summary_data, indent=2)[:2000]
        if len(json.dumps(obj.summary_data)) > 2000:
            preview += "\n... (truncated)"
        return format_html('<pre style="max-height: 400px; overflow: auto;">{}</pre>', preview)
    summary_data_preview.short_description = 'Summary Data (Preview)'

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'organization', 'created_by'
        )

    actions = ['mark_completed', 'mark_failed', 'regenerate']

    def mark_completed(self, request, queryset):
        """Mark selected reports as completed."""
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} reports marked as completed.')
    mark_completed.short_description = 'Mark as completed'

    def mark_failed(self, request, queryset):
        """Mark selected reports as failed."""
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} reports marked as failed.')
    mark_failed.short_description = 'Mark as failed'

    def regenerate(self, request, queryset):
        """Regenerate selected reports."""
        from .tasks import generate_report_async
        count = 0
        for report in queryset:
            generate_report_async.delay(str(report.pk))
            count += 1
        self.message_user(request, f'{count} reports queued for regeneration.')
    regenerate.short_description = 'Regenerate reports'
