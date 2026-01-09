"""
Analytics models for tracking insight feedback and effectiveness.

InsightFeedback tracks user actions on AI-generated insights and their outcomes,
enabling ROI measurement and continuous improvement of recommendations.
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from apps.authentication.models import Organization


class InsightFeedback(models.Model):
    """
    Track user actions and outcomes for AI-generated insights.

    Enables:
    - ROI measurement (predicted vs actual savings)
    - Recommendation effectiveness tracking
    - Historical context for AI improvement
    """

    ACTION_CHOICES = [
        ('implemented', 'Implemented'),
        ('dismissed', 'Dismissed'),
        ('deferred', 'Deferred for Later'),
        ('investigating', 'Under Investigation'),
        ('partial', 'Partially Implemented'),
    ]

    OUTCOME_CHOICES = [
        ('pending', 'Outcome Pending'),
        ('success', 'Achieved Expected Savings'),
        ('partial_success', 'Partial Savings Achieved'),
        ('no_change', 'No Measurable Impact'),
        ('failed', 'Implementation Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='insight_feedback'
    )

    # Insight identification (stored as snapshot since insights are generated dynamically)
    insight_id = models.CharField(max_length=36, db_index=True)
    insight_type = models.CharField(max_length=50, db_index=True)
    insight_title = models.CharField(max_length=200)
    insight_severity = models.CharField(max_length=20)
    predicted_savings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Predicted savings amount from the insight"
    )

    # User action tracking
    action_taken = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        db_index=True
    )
    action_date = models.DateTimeField(auto_now_add=True)
    action_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='insight_actions'
    )
    action_notes = models.TextField(blank=True)

    # Outcome tracking (updated later after implementation)
    outcome = models.CharField(
        max_length=20,
        choices=OUTCOME_CHOICES,
        default='pending',
        db_index=True
    )
    actual_savings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual savings realized after implementation"
    )
    outcome_date = models.DateTimeField(null=True, blank=True)
    outcome_notes = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-action_date']
        indexes = [
            models.Index(fields=['organization', 'insight_type']),
            models.Index(fields=['organization', 'action_taken']),
            models.Index(fields=['organization', 'outcome']),
            models.Index(fields=['action_date']),
        ]
        verbose_name = 'Insight Feedback'
        verbose_name_plural = 'Insight Feedback'

    def __str__(self):
        return f"{self.insight_type}: {self.action_taken} - {self.insight_title[:50]}"

    @property
    def savings_accuracy(self) -> float | None:
        """
        Calculate accuracy of predicted vs actual savings.

        Returns ratio of actual/predicted, or None if not applicable.
        """
        if self.actual_savings and self.predicted_savings and self.predicted_savings > 0:
            return float(self.actual_savings) / float(self.predicted_savings)
        return None

    @property
    def savings_variance(self) -> float | None:
        """
        Calculate variance between predicted and actual savings.

        Positive = actual exceeded prediction
        Negative = actual fell short of prediction
        """
        if self.actual_savings is not None and self.predicted_savings is not None:
            return float(self.actual_savings) - float(self.predicted_savings)
        return None
