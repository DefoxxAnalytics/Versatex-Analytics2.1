"""
Analytics API views
"""
from decimal import Decimal
from django.utils import timezone
from django.db.models import Count, Sum, Avg, F
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.exceptions import ValidationError
from apps.authentication.utils import log_action
from apps.authentication.models import Organization
from apps.authentication.organization_utils import get_target_organization
from .services import AnalyticsService
from .ai_services import AIInsightsService
from .models import InsightFeedback
from .predictive_services import PredictiveAnalyticsService
from .contract_services import ContractAnalyticsService
from .compliance_services import ComplianceService


def validate_int_param(request, param_name, default, min_val=1, max_val=1000):
    """
    Safely parse and validate integer query parameter.

    Args:
        request: The HTTP request object
        param_name: Name of the query parameter
        default: Default value if not provided
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Validated integer value

    Raises:
        ValidationError: If value is invalid or out of range
    """
    raw_value = request.query_params.get(param_name, default)
    try:
        value = int(raw_value)
        if value < min_val or value > max_val:
            raise ValidationError({
                param_name: f"Value must be between {min_val} and {max_val}"
            })
        return value
    except (ValueError, TypeError):
        raise ValidationError({
            param_name: f"Invalid value '{raw_value}'. Must be an integer."
        })


class ReadAPIThrottle(ScopedRateThrottle):
    """Throttle for read API endpoints."""
    scope = 'read_api'


class AIInsightsThrottle(ScopedRateThrottle):
    """Throttle for AI insights endpoints (more restrictive due to computation cost)."""
    scope = 'ai_insights'


class PredictionsThrottle(ScopedRateThrottle):
    """Throttle for predictions endpoints."""
    scope = 'predictions'


class ContractAnalyticsThrottle(ScopedRateThrottle):
    """Throttle for contract analytics endpoints."""
    scope = 'contract_analytics'


class ComplianceThrottle(ScopedRateThrottle):
    """Throttle for compliance endpoints."""
    scope = 'compliance'


class InsightFeedbackThrottle(ScopedRateThrottle):
    """Throttle for insight feedback endpoints."""
    scope = 'insight_feedback'


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def overview_stats(request):
    """
    Get overview statistics.

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(organization)
    data = service.get_overview_stats()

    log_action(
        user=request.user,
        action='view',
        resource='analytics_overview',
        request=request,
        details={'organization_id': organization.id} if request.user.is_superuser else {}
    )

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def spend_by_category(request):
    """
    Get spend breakdown by category.

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(organization)
    data = service.get_spend_by_category()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def detailed_category_stats(request):
    """
    Get detailed category analysis including subcategories, suppliers, and risk levels.

    Returns comprehensive data for the Categories dashboard page with:
    - Category totals and percentages
    - Subcategory breakdown per category
    - Supplier counts and concentration metrics
    - Risk level assessment (high/medium/low)

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(organization)
    data = service.get_detailed_category_analysis()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def spend_by_supplier(request):
    """
    Get spend breakdown by supplier.

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(organization)
    data = service.get_spend_by_supplier()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def detailed_supplier_stats(request):
    """
    Get detailed supplier analysis including HHI score, concentration metrics, and category diversity.

    Returns comprehensive data for the Suppliers dashboard page with:
    - Summary: total suppliers, total spend, HHI score, concentration metrics
    - Per-supplier: spend, percentage, transaction count, avg transaction, category count, rank

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(organization)
    data = service.get_detailed_supplier_analysis()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def supplier_drilldown(request, supplier_id):
    """
    Get detailed drill-down data for a specific supplier.
    Used by Pareto Analysis page when user clicks on a supplier.

    Returns:
    - Basic metrics: total spend, transaction count, avg transaction
    - Date range: min and max dates
    - Category breakdown with spend and percentage
    - Subcategory breakdown (top 10)
    - Location breakdown (top 10)

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(organization)
    data = service.get_supplier_drilldown(supplier_id)

    if data is None:
        return Response({'error': 'Supplier not found'}, status=404)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def monthly_trend(request):
    """
    Get monthly spend trend.

    Query params:
    - months: Number of months (default: 12)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    months = validate_int_param(request, 'months', 12, min_val=1, max_val=120)
    service = AnalyticsService(organization)
    data = service.get_monthly_trend(months=months)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def pareto_analysis(request):
    """
    Get Pareto analysis.

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(organization)
    data = service.get_pareto_analysis()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def tail_spend_analysis(request):
    """
    Get tail spend analysis.

    Query params:
    - threshold: Percentage threshold (default: 20)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    threshold = validate_int_param(request, 'threshold', 20, min_val=1, max_val=100)
    service = AnalyticsService(organization)
    data = service.get_tail_spend_analysis(threshold_percentage=threshold)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def spend_stratification(request):
    """
    Get spend stratification (Kraljic Matrix).

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(organization)
    data = service.get_spend_stratification()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def detailed_stratification(request):
    """
    Get detailed spend stratification by spend bands.

    Returns comprehensive stratification analysis including:
    - Summary metrics (active bands, strategic bands, risk assessment)
    - Spend bands breakdown (0-1K through 1M+)
    - Segments (Strategic/Leverage/Routine/Tactical)
    - Recommendations

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(organization)
    data = service.get_detailed_stratification()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def stratification_segment_drilldown(request, segment_name):
    """
    Get drill-down data for a specific stratification segment.

    Args:
        segment_name: One of 'Strategic', 'Leverage', 'Routine', 'Tactical'

    Returns detailed breakdown including:
    - Supplier list with spend and metrics
    - Top 10 subcategories
    - Top 10 locations

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(organization)
    data = service.get_stratification_segment_drilldown(segment_name)

    if data is None:
        return Response({'error': f"Invalid segment name: {segment_name}. Must be one of: Strategic, Leverage, Routine, Tactical"}, status=400)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def stratification_band_drilldown(request, band_name):
    """
    Get drill-down data for a specific spend band.

    Args:
        band_name: One of the spend bands (e.g., '0 - 1K', '1K - 2K', etc.)

    Returns detailed breakdown including:
    - Supplier list with spend and metrics
    - Top 10 subcategories
    - Top 10 locations

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(organization)
    data = service.get_stratification_band_drilldown(band_name)

    if data is None:
        return Response({
            'error': f"Invalid band name: {band_name}. Must be one of: 0 - 1K, 1K - 2K, 2K - 5K, 5K - 10K, 10K - 25K, 25K - 50K, 50K - 100K, 100K - 500K, 500K - 1M, 1M and Above"
        }, status=400)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def seasonality_analysis(request):
    """
    Get seasonality analysis.

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(organization)
    data = service.get_seasonality_analysis()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def detailed_seasonality(request):
    """
    Get detailed seasonality analysis with fiscal year support, category breakdowns,
    seasonal indices, and savings potential calculations.

    Query params:
    - use_fiscal_year: Use fiscal year (Jul-Jun) instead of calendar year (default: true)
    - organization_id (superusers only): View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    # Parse use_fiscal_year parameter (default: true)
    use_fiscal_year_param = request.query_params.get('use_fiscal_year', 'true').lower()
    use_fiscal_year = use_fiscal_year_param not in ('false', '0', 'no')

    service = AnalyticsService(organization)
    data = service.get_detailed_seasonality_analysis(use_fiscal_year=use_fiscal_year)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def seasonality_category_drilldown(request, category_id):
    """
    Get detailed seasonality drill-down for a specific category.
    Returns supplier-level seasonal patterns.

    Query params:
    - use_fiscal_year: Use fiscal year (Jul-Jun) instead of calendar year (default: true)
    - organization_id (superusers only): View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    # Parse use_fiscal_year parameter (default: true)
    use_fiscal_year_param = request.query_params.get('use_fiscal_year', 'true').lower()
    use_fiscal_year = use_fiscal_year_param not in ('false', '0', 'no')

    service = AnalyticsService(organization)
    data = service.get_seasonality_category_drilldown(category_id, use_fiscal_year=use_fiscal_year)

    if data is None:
        return Response({'error': 'Category not found'}, status=404)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def year_over_year(request):
    """
    Get year over year comparison.

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(organization)
    data = service.get_year_over_year_comparison()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def detailed_year_over_year(request):
    """
    Get detailed year over year comparison with category and supplier breakdowns.

    Query params:
    - use_fiscal_year: Whether to use fiscal year (Jul-Jun) or calendar year (default: true)
    - year1: First fiscal year to compare (optional)
    - year2: Second fiscal year to compare (optional)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    use_fiscal_year = request.query_params.get('use_fiscal_year', 'true').lower() not in ('false', '0', 'no')
    year1 = request.query_params.get('year1')
    year2 = request.query_params.get('year2')

    # Convert years to int if provided
    if year1:
        try:
            year1 = int(year1)
        except ValueError:
            year1 = None
    if year2:
        try:
            year2 = int(year2)
        except ValueError:
            year2 = None

    service = AnalyticsService(organization)
    data = service.get_detailed_year_over_year(year1=year1, year2=year2, use_fiscal_year=use_fiscal_year)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def yoy_category_drilldown(request, category_id):
    """
    Get detailed YoY comparison for a specific category.

    Query params:
    - use_fiscal_year: Whether to use fiscal year (Jul-Jun) or calendar year (default: true)
    - year1: First fiscal year to compare (optional)
    - year2: Second fiscal year to compare (optional)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    use_fiscal_year = request.query_params.get('use_fiscal_year', 'true').lower() not in ('false', '0', 'no')
    year1 = request.query_params.get('year1')
    year2 = request.query_params.get('year2')

    if year1:
        try:
            year1 = int(year1)
        except ValueError:
            year1 = None
    if year2:
        try:
            year2 = int(year2)
        except ValueError:
            year2 = None

    service = AnalyticsService(organization)
    data = service.get_yoy_category_drilldown(category_id, year1=year1, year2=year2, use_fiscal_year=use_fiscal_year)

    if data is None:
        return Response({'error': 'Category not found'}, status=404)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def yoy_supplier_drilldown(request, supplier_id):
    """
    Get detailed YoY comparison for a specific supplier.

    Query params:
    - use_fiscal_year: Whether to use fiscal year (Jul-Jun) or calendar year (default: true)
    - year1: First fiscal year to compare (optional)
    - year2: Second fiscal year to compare (optional)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    use_fiscal_year = request.query_params.get('use_fiscal_year', 'true').lower() not in ('false', '0', 'no')
    year1 = request.query_params.get('year1')
    year2 = request.query_params.get('year2')

    if year1:
        try:
            year1 = int(year1)
        except ValueError:
            year1 = None
    if year2:
        try:
            year2 = int(year2)
        except ValueError:
            year2 = None

    service = AnalyticsService(organization)
    data = service.get_yoy_supplier_drilldown(supplier_id, year1=year1, year2=year2, use_fiscal_year=use_fiscal_year)

    if data is None:
        return Response({'error': 'Supplier not found'}, status=404)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def consolidation_opportunities(request):
    """
    Get supplier consolidation opportunities.

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(organization)
    data = service.get_supplier_consolidation_opportunities()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def detailed_tail_spend(request):
    """
    Get detailed tail spend analysis using dollar threshold.

    Tail vendors are those with total spend below the threshold.
    Returns comprehensive data for the Tail Spend dashboard page including:
    - Summary stats (total vendors, tail count, tail spend, savings opportunity)
    - Segments (micro <$10K, small $10K-$50K, non-tail >$50K)
    - Pareto data (top 20 vendors with cumulative %)
    - Category analysis (tail metrics per category)
    - Consolidation opportunities

    Query params:
    - threshold: Dollar threshold for tail classification (default: 50000, range: 1000-500000)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    threshold = validate_int_param(request, 'threshold', 50000, min_val=1000, max_val=500000)

    service = AnalyticsService(organization)
    data = service.get_detailed_tail_spend(threshold=threshold)

    log_action(
        user=request.user,
        action='view',
        resource='tail_spend_detailed',
        request=request,
        details={'threshold': threshold, 'organization_id': organization.id} if request.user.is_superuser else {'threshold': threshold}
    )

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def tail_spend_category_drilldown(request, category_id):
    """
    Get detailed tail spend drill-down for a specific category.
    Returns vendor-level breakdown within the category.

    Query params:
    - threshold: Dollar threshold for tail classification (default: 50000)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    threshold = validate_int_param(request, 'threshold', 50000, min_val=1000, max_val=500000)

    service = AnalyticsService(organization)
    data = service.get_tail_spend_category_drilldown(category_id, threshold=threshold)

    if data is None:
        return Response({'error': 'Category not found'}, status=404)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def tail_spend_vendor_drilldown(request, supplier_id):
    """
    Get detailed tail spend drill-down for a specific vendor.
    Returns category breakdown, locations, and monthly spend.

    Query params:
    - threshold: Dollar threshold for tail classification (default: 50000)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    threshold = validate_int_param(request, 'threshold', 50000, min_val=1000, max_val=500000)

    service = AnalyticsService(organization)
    data = service.get_tail_spend_vendor_drilldown(supplier_id, threshold=threshold)

    if data is None:
        return Response({'error': 'Supplier not found'}, status=404)

    return Response(data)


# ============================================================================
# AI Insights Endpoints
# ============================================================================

def _get_ai_service(request, organization=None):
    """
    Helper to create AI Insights Service with user preferences.

    Args:
        request: HTTP request object
        organization: Optional organization override (for superuser org switching)
    """
    profile = request.user.profile
    ai_settings = getattr(profile, 'ai_settings', {}) or {}

    # Use provided organization or get from request
    target_org = organization or get_target_organization(request)

    return AIInsightsService(
        organization=target_org,
        use_external_ai=ai_settings.get('use_external_ai', False),
        ai_provider=ai_settings.get('ai_provider', 'anthropic'),
        api_key=ai_settings.get('ai_api_key', None)
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIInsightsThrottle])
def ai_insights(request):
    """
    Get all AI-powered insights.

    Returns combined insights from all analysis types:
    - Cost optimization
    - Supplier risk
    - Anomaly detection
    - Consolidation recommendations

    Query params:
    - refresh: Set to 'true' to bypass cache and regenerate AI enhancement

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    force_refresh = request.query_params.get('refresh', 'false').lower() == 'true'

    service = _get_ai_service(request, organization)
    data = service.get_all_insights(force_refresh=force_refresh)

    log_details = {
        'insight_count': data['summary']['total_insights'],
        'cache_hit': data.get('cache_hit', False),
        'ai_enhanced': 'ai_enhancement' in data,
    }
    if request.user.is_superuser:
        log_details['organization_id'] = organization.id

    log_action(
        user=request.user,
        action='view',
        resource='ai_insights',
        request=request,
        details=log_details
    )

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIInsightsThrottle])
def ai_insights_cost(request):
    """
    Get cost optimization insights only.

    Identifies price variance across suppliers and potential savings.

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = _get_ai_service(request, organization)
    insights = service.get_cost_optimization_insights()

    return Response({
        'insights': insights,
        'count': len(insights)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIInsightsThrottle])
def ai_insights_risk(request):
    """
    Get supplier risk insights only.

    Identifies supplier concentration and dependency risks.

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = _get_ai_service(request, organization)
    insights = service.get_supplier_risk_insights()

    return Response({
        'insights': insights,
        'count': len(insights)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIInsightsThrottle])
def ai_insights_anomalies(request):
    """
    Get anomaly detection insights.

    Uses statistical analysis to find unusual transactions.

    Query params:
    - sensitivity: Z-score threshold (default: 2.0, range: 1.0-5.0)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    # Parse sensitivity parameter
    try:
        sensitivity = float(request.query_params.get('sensitivity', 2.0))
        sensitivity = max(1.0, min(5.0, sensitivity))  # Clamp to range
    except (ValueError, TypeError):
        sensitivity = 2.0

    service = _get_ai_service(request, organization)
    insights = service.get_anomaly_insights(sensitivity=sensitivity)

    return Response({
        'insights': insights,
        'count': len(insights),
        'sensitivity': sensitivity
    })


# ============================================================================
# Async AI Enhancement Endpoints
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIInsightsThrottle])
def request_ai_enhancement(request):
    """
    Request async AI enhancement for insights.

    Triggers a background Celery task to enhance insights with external AI.
    Results are stored in cache and can be polled via get_ai_enhancement_status.

    Request body:
    - insights: List of insight objects to enhance (required)

    Query params (superusers only):
    - organization_id: Enhance insights for a specific organization
    """
    from .tasks import enhance_insights_async

    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    insights_data = request.data.get('insights', [])
    if not insights_data:
        return Response({'error': 'insights list is required'}, status=400)

    if not isinstance(insights_data, list):
        return Response({'error': 'insights must be a list'}, status=400)

    task = enhance_insights_async.delay(
        org_id=organization.id,
        user_id=request.user.id,
        insights_data=insights_data
    )

    log_action(
        user=request.user,
        action='create',
        resource='ai_enhancement_task',
        resource_id=task.id,
        request=request,
        details={
            'insight_count': len(insights_data),
            'organization_id': organization.id
        } if request.user.is_superuser else {
            'insight_count': len(insights_data)
        }
    )

    return Response({
        'task_id': task.id,
        'status': 'queued',
        'message': 'AI enhancement task queued successfully'
    }, status=202)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIInsightsThrottle])
def get_ai_enhancement_status(request):
    """
    Poll for async AI enhancement status and results.

    Returns the current status of the enhancement task and results if completed.

    Query params (superusers only):
    - organization_id: Get status for a specific organization
    """
    from django.core.cache import cache
    from .tasks import ENHANCEMENT_STATUS_PREFIX, ENHANCEMENT_RESULT_PREFIX

    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    status_key = f"{ENHANCEMENT_STATUS_PREFIX}:{organization.id}:{request.user.id}"
    result_key = f"{ENHANCEMENT_RESULT_PREFIX}:{organization.id}:{request.user.id}"

    status_data = cache.get(status_key)
    if status_data is None:
        return Response({
            'status': 'not_found',
            'message': 'No enhancement task found. Start one with POST /api/v1/analytics/ai/enhance/request/'
        })

    response_data = {
        'status': status_data.get('status', 'unknown'),
        'progress': status_data.get('progress', 0),
    }

    if status_data.get('status') == 'completed':
        result_data = cache.get(result_key)
        if result_data:
            response_data['enhancement'] = result_data
    elif status_data.get('status') == 'failed':
        response_data['error'] = status_data.get('error', 'Unknown error')

    return Response(response_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIInsightsThrottle])
def request_deep_analysis(request):
    """
    Request deep analysis for a specific insight.

    Triggers a background Celery task to perform comprehensive analysis
    including root cause analysis, implementation roadmap, and financial impact.

    Request body:
    - insight: The insight object to analyze (required)

    Query params (superusers only):
    - organization_id: Analyze insight for a specific organization
    """
    from .tasks import perform_deep_analysis_async

    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    insight_data = request.data.get('insight')
    if not insight_data:
        return Response({'error': 'insight object is required'}, status=400)

    if not isinstance(insight_data, dict):
        return Response({'error': 'insight must be an object'}, status=400)

    if 'id' not in insight_data:
        return Response({'error': 'insight must have an id field'}, status=400)

    task = perform_deep_analysis_async.delay(
        org_id=organization.id,
        user_id=request.user.id,
        insight_data=insight_data
    )

    log_action(
        user=request.user,
        action='create',
        resource='deep_analysis_task',
        resource_id=task.id,
        request=request,
        details={
            'insight_id': insight_data.get('id'),
            'insight_type': insight_data.get('type'),
            'organization_id': organization.id
        } if request.user.is_superuser else {
            'insight_id': insight_data.get('id'),
            'insight_type': insight_data.get('type')
        }
    )

    return Response({
        'task_id': task.id,
        'insight_id': insight_data.get('id'),
        'status': 'queued',
        'message': 'Deep analysis task queued successfully'
    }, status=202)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIInsightsThrottle])
def get_deep_analysis_status(request, insight_id):
    """
    Poll for deep analysis status and results for a specific insight.

    Args:
        insight_id: The ID of the insight being analyzed

    Query params (superusers only):
    - organization_id: Get status for a specific organization
    """
    from django.core.cache import cache

    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    status_key = f"deep_analysis_status:{organization.id}:{insight_id}"
    result_key = f"deep_analysis_result:{organization.id}:{insight_id}"

    status_data = cache.get(status_key)
    if status_data is None:
        return Response({
            'status': 'not_found',
            'insight_id': insight_id,
            'message': 'No deep analysis task found for this insight'
        })

    response_data = {
        'status': status_data.get('status', 'unknown'),
        'progress': status_data.get('progress', 0),
        'insight_id': insight_id,
    }

    if status_data.get('status') == 'completed':
        result_data = cache.get(result_key)
        if result_data:
            response_data['analysis'] = result_data
    elif status_data.get('status') == 'failed':
        response_data['error'] = status_data.get('error', 'Unknown error')

    return Response(response_data)


# ============================================================================
# AI Insights Metrics & Monitoring Endpoints
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_insights_metrics(request):
    """
    Get AI insights metrics for monitoring and alerting.

    Returns comprehensive metrics including:
    - Cache statistics (hits, misses, hit rate)
    - Provider health status
    - Usage statistics

    This endpoint is designed to be scraped by Prometheus or other
    monitoring systems for alerting integration.

    Query params (superusers only):
    - organization_id: Get metrics for a specific organization
    - include_health_check: If 'true', perform live provider health checks (slower)
    """
    from .ai_cache import AIInsightsCache

    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    include_health_check = request.query_params.get('include_health_check', 'false').lower() == 'true'

    # Get cache statistics
    cache_stats = AIInsightsCache.get_cache_stats(organization.id)

    # Get AI service for provider status
    service = _get_ai_service(request, organization)
    provider_status = service.get_provider_status()

    # Perform health checks if requested (adds latency)
    provider_health = {}
    if include_health_check:
        provider_health = service.health_check_providers()

    metrics = {
        'organization_id': organization.id,
        'organization_name': organization.name,
        'timestamp': timezone.now().isoformat(),
        'cache': {
            'hits': cache_stats.get('hits', 0),
            'misses': cache_stats.get('misses', 0),
            'hit_rate': cache_stats.get('hit_rate', 0),
            'total_requests': cache_stats.get('total_requests', 0),
        },
        'providers': {
            'primary': provider_status.get('primary_provider'),
            'fallback_enabled': provider_status.get('fallback_enabled', False),
            'available': provider_status.get('available_providers', []),
            'last_successful': provider_status.get('last_successful_provider'),
            'errors': provider_status.get('provider_errors', {}),
            'status': provider_status.get('providers', {}),
        },
    }

    if provider_health:
        metrics['health_checks'] = provider_health

    log_action(
        user=request.user,
        action='view',
        resource='ai_insights_metrics',
        request=request,
        details={'organization_id': organization.id, 'include_health_check': include_health_check}
        if request.user.is_superuser else {'include_health_check': include_health_check}
    )

    return Response(metrics)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_insights_metrics_prometheus(request):
    """
    Get AI insights metrics in Prometheus format.

    Returns metrics in Prometheus text exposition format for direct scraping.
    Useful for integrating with Prometheus/Grafana monitoring stack.

    Query params (superusers only):
    - organization_id: Get metrics for a specific organization
    """
    from django.http import HttpResponse
    from .ai_cache import AIInsightsCache

    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    cache_stats = AIInsightsCache.get_cache_stats(organization.id)
    service = _get_ai_service(request, organization)
    provider_status = service.get_provider_status()

    org_id = organization.id
    org_name = organization.name.replace('"', '\\"')

    lines = [
        '# HELP ai_insights_cache_hits_total Total number of cache hits',
        '# TYPE ai_insights_cache_hits_total counter',
        f'ai_insights_cache_hits_total{{org_id="{org_id}",org_name="{org_name}"}} {cache_stats.get("hits", 0)}',
        '',
        '# HELP ai_insights_cache_misses_total Total number of cache misses',
        '# TYPE ai_insights_cache_misses_total counter',
        f'ai_insights_cache_misses_total{{org_id="{org_id}",org_name="{org_name}"}} {cache_stats.get("misses", 0)}',
        '',
        '# HELP ai_insights_cache_hit_rate Cache hit rate percentage',
        '# TYPE ai_insights_cache_hit_rate gauge',
        f'ai_insights_cache_hit_rate{{org_id="{org_id}",org_name="{org_name}"}} {cache_stats.get("hit_rate", 0)}',
        '',
        '# HELP ai_insights_cache_requests_total Total cache requests',
        '# TYPE ai_insights_cache_requests_total counter',
        f'ai_insights_cache_requests_total{{org_id="{org_id}",org_name="{org_name}"}} {cache_stats.get("total_requests", 0)}',
        '',
        '# HELP ai_insights_provider_available Provider availability (1=available, 0=unavailable)',
        '# TYPE ai_insights_provider_available gauge',
    ]

    for provider_name, status in provider_status.get('providers', {}).items():
        available = 1 if status.get('available', False) else 0
        lines.append(
            f'ai_insights_provider_available{{org_id="{org_id}",provider="{provider_name}"}} {available}'
        )

    lines.extend([
        '',
        '# HELP ai_insights_fallback_enabled Whether provider fallback is enabled',
        '# TYPE ai_insights_fallback_enabled gauge',
        f'ai_insights_fallback_enabled{{org_id="{org_id}"}} {1 if provider_status.get("fallback_enabled") else 0}',
    ])

    metrics_text = '\n'.join(lines) + '\n'

    return HttpResponse(
        metrics_text,
        content_type='text/plain; version=0.0.4; charset=utf-8'
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_insights_cache_invalidate(request):
    """
    Manually invalidate AI insights cache for the organization.

    Useful for forcing cache refresh after configuration changes
    or when troubleshooting stale data issues.

    Query params (superusers only):
    - organization_id: Invalidate cache for a specific organization
    """
    from .ai_cache import AIInsightsCache

    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    invalidated_count = AIInsightsCache.invalidate_org_cache(organization.id)

    log_action(
        user=request.user,
        action='delete',
        resource='ai_insights_cache',
        request=request,
        details={
            'organization_id': organization.id,
            'invalidated_count': invalidated_count
        } if request.user.is_superuser else {
            'invalidated_count': invalidated_count
        }
    )

    return Response({
        'message': 'Cache invalidated successfully',
        'organization_id': organization.id,
        'invalidated_entries': invalidated_count
    })


# ============================================================================
# Predictive Analytics Endpoints
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([PredictionsThrottle])
def spending_forecast(request):
    """
    Get spending forecast for the next N months.

    Query params:
    - months: Number of months to forecast (default: 6, range: 1-24)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    months = validate_int_param(request, 'months', 6, min_val=1, max_val=24)

    service = PredictiveAnalyticsService(organization)
    data = service.get_spending_forecast(months=months)

    log_action(
        user=request.user,
        action='view',
        resource='spending_forecast',
        request=request,
        details={'months': months, 'organization_id': organization.id} if request.user.is_superuser else {'months': months}
    )

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([PredictionsThrottle])
def category_forecast(request, category_id):
    """
    Get spending forecast for a specific category.

    Query params:
    - months: Number of months to forecast (default: 6, range: 1-24)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    months = validate_int_param(request, 'months', 6, min_val=1, max_val=24)

    service = PredictiveAnalyticsService(organization)
    data = service.get_category_forecast(category_id=category_id, months=months)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([PredictionsThrottle])
def supplier_forecast(request, supplier_id):
    """
    Get spending forecast for a specific supplier.

    Query params:
    - months: Number of months to forecast (default: 6, range: 1-24)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    months = validate_int_param(request, 'months', 6, min_val=1, max_val=24)

    service = PredictiveAnalyticsService(organization)
    data = service.get_supplier_forecast(supplier_id=supplier_id, months=months)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([PredictionsThrottle])
def trend_analysis(request):
    """
    Get comprehensive trend analysis across all dimensions.

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = PredictiveAnalyticsService(organization)
    data = service.get_trend_analysis()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([PredictionsThrottle])
def budget_projection(request):
    """
    Compare forecast against budget and project year-end position.

    Query params:
    - annual_budget: Annual budget amount (required)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    try:
        annual_budget = float(request.query_params.get('annual_budget', 0))
        if annual_budget <= 0:
            return Response(
                {'error': 'annual_budget must be a positive number'},
                status=400
            )
    except (ValueError, TypeError):
        return Response(
            {'error': 'annual_budget must be a valid number'},
            status=400
        )

    service = PredictiveAnalyticsService(organization)
    data = service.get_budget_projection(annual_budget=annual_budget)

    return Response(data)


# ============================================================================
# Contract Analytics Endpoints
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ContractAnalyticsThrottle])
def contract_overview(request):
    """
    Get contract overview statistics.

    Returns summary of contract portfolio including:
    - Total contracts, active count, total/annual value
    - Contract coverage percentage
    - Expiring contracts count

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = ContractAnalyticsService(organization)
    data = service.get_contract_overview()

    log_action(
        user=request.user,
        action='view',
        resource='contract_overview',
        request=request,
        details={'organization_id': organization.id} if request.user.is_superuser else {}
    )

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ContractAnalyticsThrottle])
def contracts_list(request):
    """
    List all contracts with basic information.

    Returns list of contracts including:
    - Contract details (number, title, supplier, value)
    - Status and dates
    - Days until expiry

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = ContractAnalyticsService(organization)
    data = service.get_contracts_list()

    return Response({
        'contracts': data,
        'count': len(data)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ContractAnalyticsThrottle])
def contract_detail(request, contract_id):
    """
    Get detailed information for a specific contract.

    Returns:
    - Full contract details
    - Performance metrics (utilization, monthly spend)
    - Category breakdown

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = ContractAnalyticsService(organization)
    data = service.get_contract_detail(contract_id)

    if data is None:
        return Response({'error': 'Contract not found'}, status=404)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ContractAnalyticsThrottle])
def expiring_contracts(request):
    """
    Get contracts expiring within specified days.

    Query params:
    - days: Number of days to look ahead (default: 90, range: 1-365)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    days = validate_int_param(request, 'days', 90, min_val=1, max_val=365)

    service = ContractAnalyticsService(organization)
    data = service.get_expiring_contracts(days=days)

    return Response({
        'contracts': data,
        'count': len(data),
        'days_threshold': days
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ContractAnalyticsThrottle])
def contract_performance(request, contract_id):
    """
    Get detailed performance metrics for a specific contract.

    Returns:
    - Utilization metrics
    - Monthly spending trends
    - Supplier performance

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = ContractAnalyticsService(organization)
    data = service.get_contract_performance(contract_id)

    if data is None:
        return Response({'error': 'Contract not found'}, status=404)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ContractAnalyticsThrottle])
def contract_savings_opportunities(request):
    """
    Identify savings opportunities across contracts.

    Returns:
    - Underutilized contracts (potential renegotiation)
    - Off-contract spending (consolidation opportunities)
    - Similar category consolidation

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = ContractAnalyticsService(organization)
    data = service.get_savings_opportunities()

    log_action(
        user=request.user,
        action='view',
        resource='contract_savings',
        request=request,
        details={'organization_id': organization.id} if request.user.is_superuser else {}
    )

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ContractAnalyticsThrottle])
def contract_renewals(request):
    """
    Get renewal recommendations for contracts.

    Returns list of contracts with renewal recommendations based on:
    - Utilization rates
    - Days until expiry
    - Spend trends

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = ContractAnalyticsService(organization)
    data = service.get_renewal_recommendations()

    return Response({
        'recommendations': data,
        'count': len(data)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ContractAnalyticsThrottle])
def contract_vs_actual(request):
    """
    Compare contracted values vs actual spending.

    Query params:
    - contract_id: Optional specific contract (default: all contracts)
    - organization_id: View data for a specific organization (superusers only)

    Returns:
    - Contract value vs actual spend
    - Variance analysis
    - Monthly comparison trend
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    contract_id = request.query_params.get('contract_id')
    if contract_id:
        try:
            contract_id = int(contract_id)
        except (ValueError, TypeError):
            return Response({'error': 'contract_id must be an integer'}, status=400)

    service = ContractAnalyticsService(organization)
    data = service.get_contract_vs_actual_spend(contract_id=contract_id)

    return Response(data)


# ============================================================================
# Compliance & Maverick Spend Endpoints
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ComplianceThrottle])
def compliance_overview(request):
    """
    Get compliance overview statistics.

    Returns:
    - Compliance rate
    - Violation counts by severity
    - Maverick spend metrics
    - Active policies count

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = ComplianceService(organization)
    data = service.get_compliance_overview()

    log_action(
        user=request.user,
        action='view',
        resource='compliance_overview',
        request=request,
        details={'organization_id': organization.id} if request.user.is_superuser else {}
    )

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ComplianceThrottle])
def maverick_spend_analysis(request):
    """
    Get detailed maverick (off-contract) spend analysis.

    Returns:
    - Maverick spend by supplier
    - Maverick spend by category
    - Recommendations for reducing maverick spend

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = ComplianceService(organization)
    data = service.get_maverick_spend_analysis()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ComplianceThrottle])
def policy_violations(request):
    """
    Get policy violations with optional filtering.

    Query params:
    - resolved: Filter by resolution status (true/false)
    - severity: Filter by severity (critical/high/medium/low)
    - limit: Maximum number of violations to return (default: 100)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    # Parse resolved filter
    resolved_param = request.query_params.get('resolved')
    resolved = None
    if resolved_param is not None:
        resolved = resolved_param.lower() == 'true'

    # Parse severity filter
    severity = request.query_params.get('severity')
    if severity and severity not in ['critical', 'high', 'medium', 'low']:
        severity = None

    # Parse limit
    limit = validate_int_param(request, 'limit', 100, min_val=1, max_val=500)

    service = ComplianceService(organization)
    data = service.get_policy_violations(resolved=resolved, severity=severity, limit=limit)

    return Response({
        'violations': data,
        'count': len(data)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ComplianceThrottle])
def violation_trends(request):
    """
    Get violation trends over time.

    Query params:
    - months: Number of months to analyze (default: 12)
    - organization_id: View data for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    months = validate_int_param(request, 'months', 12, min_val=1, max_val=36)

    service = ComplianceService(organization)
    data = service.get_violation_trends(months=months)

    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([ComplianceThrottle])
def resolve_violation(request, violation_id):
    """
    Resolve a policy violation.

    Request body:
    - resolution_notes: Notes explaining the resolution (required)

    Query params (superusers only):
    - organization_id: Resolve violation for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    resolution_notes = request.data.get('resolution_notes', '')
    if not resolution_notes:
        return Response({'error': 'resolution_notes is required'}, status=400)

    service = ComplianceService(organization)
    data = service.resolve_violation(
        violation_id=violation_id,
        user=request.user,
        resolution_notes=resolution_notes
    )

    if data is None:
        return Response({'error': 'Violation not found'}, status=404)

    log_action(
        user=request.user,
        action='update',
        resource='policy_violation',
        resource_id=violation_id,
        request=request,
        details={
            'resolution_notes': resolution_notes,
            'organization_id': organization.id
        } if request.user.is_superuser else {'resolution_notes': resolution_notes}
    )

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ComplianceThrottle])
def supplier_compliance_scores(request):
    """
    Get compliance scores for all suppliers.

    Returns suppliers ranked by compliance score with:
    - Transaction count
    - Violation count
    - Contract status
    - Risk level

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = ComplianceService(organization)
    data = service.get_supplier_compliance_scores()

    return Response({
        'suppliers': data,
        'count': len(data)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ComplianceThrottle])
def spending_policies(request):
    """
    Get list of all spending policies.

    Returns active policies with rule summaries and violation counts.

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = ComplianceService(organization)
    data = service.get_policies_list()

    return Response({
        'policies': data,
        'count': len(data)
    })


# ============================================================================
# AI Insight Feedback Endpoints
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([InsightFeedbackThrottle])
def record_insight_feedback(request):
    """
    Record user action on an AI-generated insight.

    Request body:
    - insight_id: UUID of the insight (required)
    - insight_type: Type of insight (required)
    - insight_title: Title of the insight (required)
    - insight_severity: Severity level (required)
    - predicted_savings: Predicted savings amount (optional)
    - action_taken: User action (required) - implemented, dismissed, deferred, investigating, partial
    - action_notes: Optional notes about the action

    Query params (superusers only):
    - organization_id: Record feedback for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    required_fields = ['insight_id', 'insight_type', 'insight_title', 'insight_severity', 'action_taken']
    for field in required_fields:
        if not request.data.get(field):
            return Response({'error': f'{field} is required'}, status=400)

    action_taken = request.data.get('action_taken')
    valid_actions = ['implemented', 'dismissed', 'deferred', 'investigating', 'partial']
    if action_taken not in valid_actions:
        return Response({
            'error': f'Invalid action_taken. Must be one of: {", ".join(valid_actions)}'
        }, status=400)

    predicted_savings = request.data.get('predicted_savings')
    if predicted_savings is not None:
        try:
            predicted_savings = Decimal(str(predicted_savings))
        except (ValueError, TypeError):
            return Response({'error': 'predicted_savings must be a valid number'}, status=400)

    feedback = InsightFeedback.objects.create(
        organization=organization,
        insight_id=request.data.get('insight_id'),
        insight_type=request.data.get('insight_type'),
        insight_title=request.data.get('insight_title'),
        insight_severity=request.data.get('insight_severity'),
        predicted_savings=predicted_savings,
        action_taken=action_taken,
        action_by=request.user,
        action_notes=request.data.get('action_notes', '')
    )

    log_action(
        user=request.user,
        action='create',
        resource='insight_feedback',
        resource_id=str(feedback.id),
        request=request,
        details={
            'insight_type': feedback.insight_type,
            'action_taken': feedback.action_taken,
            'organization_id': organization.id
        } if request.user.is_superuser else {
            'insight_type': feedback.insight_type,
            'action_taken': feedback.action_taken
        }
    )

    return Response({
        'id': str(feedback.id),
        'insight_id': feedback.insight_id,
        'insight_type': feedback.insight_type,
        'insight_title': feedback.insight_title,
        'action_taken': feedback.action_taken,
        'action_date': feedback.action_date.isoformat(),
        'outcome': feedback.outcome,
        'message': 'Feedback recorded successfully'
    }, status=201)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@throttle_classes([InsightFeedbackThrottle])
def update_insight_outcome(request, feedback_id):
    """
    Update the outcome of a previously recorded insight action.

    Used when the results of implementing an insight are known.

    Request body:
    - outcome: Outcome status (required) - pending, success, partial_success, no_change, failed
    - actual_savings: Actual savings realized (optional)
    - outcome_notes: Notes about the outcome (optional)

    Query params (superusers only):
    - organization_id: Update feedback for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    try:
        feedback = InsightFeedback.objects.get(id=feedback_id, organization=organization)
    except InsightFeedback.DoesNotExist:
        return Response({'error': 'Feedback not found'}, status=404)

    outcome = request.data.get('outcome')
    if outcome:
        valid_outcomes = ['pending', 'success', 'partial_success', 'no_change', 'failed']
        if outcome not in valid_outcomes:
            return Response({
                'error': f'Invalid outcome. Must be one of: {", ".join(valid_outcomes)}'
            }, status=400)
        feedback.outcome = outcome
        feedback.outcome_date = timezone.now()

    actual_savings = request.data.get('actual_savings')
    if actual_savings is not None:
        try:
            feedback.actual_savings = Decimal(str(actual_savings))
        except (ValueError, TypeError):
            return Response({'error': 'actual_savings must be a valid number'}, status=400)

    outcome_notes = request.data.get('outcome_notes')
    if outcome_notes is not None:
        feedback.outcome_notes = outcome_notes

    feedback.save()

    log_action(
        user=request.user,
        action='update',
        resource='insight_feedback',
        resource_id=str(feedback.id),
        request=request,
        details={
            'outcome': feedback.outcome,
            'actual_savings': float(feedback.actual_savings) if feedback.actual_savings else None,
            'organization_id': organization.id
        } if request.user.is_superuser else {
            'outcome': feedback.outcome,
            'actual_savings': float(feedback.actual_savings) if feedback.actual_savings else None
        }
    )

    return Response({
        'id': str(feedback.id),
        'insight_id': feedback.insight_id,
        'insight_type': feedback.insight_type,
        'action_taken': feedback.action_taken,
        'outcome': feedback.outcome,
        'outcome_date': feedback.outcome_date.isoformat() if feedback.outcome_date else None,
        'predicted_savings': float(feedback.predicted_savings) if feedback.predicted_savings else None,
        'actual_savings': float(feedback.actual_savings) if feedback.actual_savings else None,
        'savings_accuracy': feedback.savings_accuracy,
        'savings_variance': feedback.savings_variance,
        'message': 'Outcome updated successfully'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([InsightFeedbackThrottle])
def get_insight_effectiveness(request):
    """
    Get effectiveness metrics for AI insights.

    Returns aggregate statistics on insight actions and outcomes to measure ROI.

    Query params (superusers only):
    - organization_id: Get effectiveness for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    feedback_qs = InsightFeedback.objects.filter(organization=organization)

    total_feedback = feedback_qs.count()
    if total_feedback == 0:
        return Response({
            'total_feedback': 0,
            'message': 'No insight feedback recorded yet'
        })

    action_breakdown = list(
        feedback_qs.values('action_taken')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    outcome_breakdown = list(
        feedback_qs.exclude(outcome='pending')
        .values('outcome')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    type_breakdown = list(
        feedback_qs.values('insight_type')
        .annotate(
            count=Count('id'),
            total_predicted=Sum('predicted_savings'),
            total_actual=Sum('actual_savings')
        )
        .order_by('-count')
    )

    savings_metrics = feedback_qs.filter(
        action_taken='implemented',
        predicted_savings__isnull=False
    ).aggregate(
        total_predicted=Sum('predicted_savings'),
        total_actual=Sum('actual_savings'),
        avg_predicted=Avg('predicted_savings'),
        avg_actual=Avg('actual_savings'),
        implemented_count=Count('id')
    )

    successful_implementations = feedback_qs.filter(
        action_taken='implemented',
        outcome__in=['success', 'partial_success']
    ).count()

    implemented_total = feedback_qs.filter(action_taken='implemented').count()
    success_rate = (successful_implementations / implemented_total * 100) if implemented_total > 0 else 0

    total_predicted = savings_metrics['total_predicted'] or Decimal('0')
    total_actual = savings_metrics['total_actual'] or Decimal('0')
    roi_accuracy = (float(total_actual) / float(total_predicted) * 100) if total_predicted > 0 else None

    return Response({
        'total_feedback': total_feedback,
        'action_breakdown': action_breakdown,
        'outcome_breakdown': outcome_breakdown,
        'type_breakdown': [
            {
                'insight_type': item['insight_type'],
                'count': item['count'],
                'total_predicted': float(item['total_predicted']) if item['total_predicted'] else 0,
                'total_actual': float(item['total_actual']) if item['total_actual'] else 0
            }
            for item in type_breakdown
        ],
        'savings_metrics': {
            'total_predicted_savings': float(total_predicted),
            'total_actual_savings': float(total_actual),
            'avg_predicted_savings': float(savings_metrics['avg_predicted']) if savings_metrics['avg_predicted'] else 0,
            'avg_actual_savings': float(savings_metrics['avg_actual']) if savings_metrics['avg_actual'] else 0,
            'implemented_insights': savings_metrics['implemented_count'] or 0,
            'roi_accuracy_percent': roi_accuracy,
            'savings_variance': float(total_actual - total_predicted)
        },
        'implementation_success_rate': round(success_rate, 1),
        'successful_implementations': successful_implementations,
        'total_implemented': implemented_total
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([InsightFeedbackThrottle])
def list_insight_feedback(request):
    """
    List all insight feedback for the organization.

    Query params:
    - insight_type: Filter by insight type (optional)
    - action_taken: Filter by action (optional)
    - outcome: Filter by outcome (optional)
    - limit: Maximum number to return (default: 50, max: 200)
    - offset: Pagination offset (default: 0)
    - organization_id: View feedback for a specific organization (superusers only)
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    feedback_qs = InsightFeedback.objects.filter(organization=organization)

    insight_type = request.query_params.get('insight_type')
    if insight_type:
        feedback_qs = feedback_qs.filter(insight_type=insight_type)

    action_taken = request.query_params.get('action_taken')
    if action_taken:
        feedback_qs = feedback_qs.filter(action_taken=action_taken)

    outcome = request.query_params.get('outcome')
    if outcome:
        feedback_qs = feedback_qs.filter(outcome=outcome)

    total_count = feedback_qs.count()

    limit = validate_int_param(request, 'limit', 50, min_val=1, max_val=200)
    offset = validate_int_param(request, 'offset', 0, min_val=0, max_val=10000)

    feedback_list = feedback_qs.order_by('-action_date')[offset:offset + limit]

    results = []
    for fb in feedback_list:
        results.append({
            'id': str(fb.id),
            'insight_id': fb.insight_id,
            'insight_type': fb.insight_type,
            'insight_title': fb.insight_title,
            'insight_severity': fb.insight_severity,
            'predicted_savings': float(fb.predicted_savings) if fb.predicted_savings else None,
            'action_taken': fb.action_taken,
            'action_date': fb.action_date.isoformat(),
            'action_by': fb.action_by.username if fb.action_by else None,
            'action_notes': fb.action_notes,
            'outcome': fb.outcome,
            'actual_savings': float(fb.actual_savings) if fb.actual_savings else None,
            'outcome_date': fb.outcome_date.isoformat() if fb.outcome_date else None,
            'outcome_notes': fb.outcome_notes,
            'savings_accuracy': fb.savings_accuracy,
            'savings_variance': fb.savings_variance
        })

    return Response({
        'feedback': results,
        'count': len(results),
        'total': total_count,
        'limit': limit,
        'offset': offset
    })
