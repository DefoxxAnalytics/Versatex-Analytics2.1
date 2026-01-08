"""
Analytics API views
"""
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

    Query params (superusers only):
    - organization_id: View data for a specific organization
    """
    organization = get_target_organization(request)
    if organization is None:
        return Response({'error': 'User profile not found'}, status=400)

    service = _get_ai_service(request, organization)
    data = service.get_all_insights()

    log_action(
        user=request.user,
        action='view',
        resource='ai_insights',
        request=request,
        details={
            'insight_count': data['summary']['total_insights'],
            'organization_id': organization.id
        } if request.user.is_superuser else {'insight_count': data['summary']['total_insights']}
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
