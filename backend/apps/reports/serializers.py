"""
Serializers for the reports module.
"""
from rest_framework import serializers
from .models import Report


class ReportListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing reports (lightweight).
    """
    created_by_name = serializers.CharField(
        source='created_by.username',
        read_only=True
    )
    report_type_display = serializers.CharField(
        source='get_report_type_display',
        read_only=True
    )
    report_format_display = serializers.CharField(
        source='get_report_format_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'name', 'description', 'report_type', 'report_type_display',
            'report_format', 'report_format_display', 'status', 'status_display',
            'period_start', 'period_end', 'created_by_name', 'created_at',
            'generated_at', 'is_expired', 'file_size', 'is_scheduled',
            'schedule_frequency', 'next_run'
        ]


class ReportDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for report detail view (includes summary_data).
    """
    created_by_name = serializers.CharField(
        source='created_by.username',
        read_only=True
    )
    organization_name = serializers.CharField(
        source='organization.name',
        read_only=True
    )
    report_type_display = serializers.CharField(
        source='get_report_type_display',
        read_only=True
    )
    report_format_display = serializers.CharField(
        source='get_report_format_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    schedule_frequency_display = serializers.CharField(
        source='get_schedule_frequency_display',
        read_only=True
    )
    is_expired = serializers.BooleanField(read_only=True)
    shared_with_users = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id', 'name', 'description', 'report_type', 'report_type_display',
            'report_format', 'report_format_display', 'organization_name',
            'period_start', 'period_end', 'filters', 'parameters',
            'status', 'status_display', 'error_message', 'file_path', 'file_size',
            'summary_data', 'is_public', 'shared_with_users', 'is_scheduled',
            'schedule_frequency', 'schedule_frequency_display', 'next_run', 'last_run',
            'created_by_name', 'created_at', 'updated_at', 'generated_at', 'is_expired'
        ]

    def get_shared_with_users(self, obj):
        """Get list of usernames the report is shared with."""
        return list(obj.shared_with.values_list('username', flat=True))


class ReportGenerateSerializer(serializers.Serializer):
    """
    Serializer for generating a new report.
    """
    report_type = serializers.ChoiceField(choices=Report.REPORT_TYPE_CHOICES)
    report_format = serializers.ChoiceField(
        choices=Report.REPORT_FORMAT_CHOICES,
        default='pdf'
    )
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    period_start = serializers.DateField(required=False, allow_null=True)
    period_end = serializers.DateField(required=False, allow_null=True)
    filters = serializers.JSONField(required=False, default=dict)
    parameters = serializers.JSONField(required=False, default=dict)
    async_generation = serializers.BooleanField(default=False)

    def validate(self, attrs):
        """Validate date range."""
        period_start = attrs.get('period_start')
        period_end = attrs.get('period_end')
        if period_start and period_end and period_start > period_end:
            raise serializers.ValidationError({
                'period_end': 'End date must be after start date.'
            })
        return attrs


class ReportScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for scheduling reports.
    """
    class Meta:
        model = Report
        fields = [
            'id', 'name', 'report_type', 'report_format', 'period_start', 'period_end',
            'filters', 'parameters', 'is_scheduled', 'schedule_frequency',
            'next_run', 'last_run'
        ]
        read_only_fields = ['id', 'next_run', 'last_run']

    def validate(self, attrs):
        """Validate scheduling configuration."""
        is_scheduled = attrs.get('is_scheduled', False)
        schedule_frequency = attrs.get('schedule_frequency', '')

        if is_scheduled and not schedule_frequency:
            raise serializers.ValidationError({
                'schedule_frequency': 'Schedule frequency is required when scheduling is enabled.'
            })
        return attrs


class ReportShareSerializer(serializers.Serializer):
    """
    Serializer for sharing reports with users.
    """
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )
    is_public = serializers.BooleanField(required=False)


class ReportTemplateSerializer(serializers.Serializer):
    """
    Serializer for report templates (predefined report configurations).
    """
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    report_type = serializers.CharField()
    icon = serializers.CharField(required=False)
    default_parameters = serializers.DictField(required=False)


class ReportStatusSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for polling report generation status.
    """
    class Meta:
        model = Report
        fields = ['id', 'status', 'error_message', 'generated_at', 'file_size']
