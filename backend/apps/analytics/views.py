"""
Analytics API views
"""
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.exceptions import ValidationError
from apps.authentication.utils import log_action
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
    Get overview statistics
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(request.user.profile.organization)
    data = service.get_overview_stats()

    log_action(
        user=request.user,
        action='view',
        resource='analytics_overview',
        request=request
    )

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def spend_by_category(request):
    """
    Get spend breakdown by category
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(request.user.profile.organization)
    data = service.get_spend_by_category()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def spend_by_supplier(request):
    """
    Get spend breakdown by supplier
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(request.user.profile.organization)
    data = service.get_spend_by_supplier()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def monthly_trend(request):
    """
    Get monthly spend trend
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    months = validate_int_param(request, 'months', 12, min_val=1, max_val=120)
    service = AnalyticsService(request.user.profile.organization)
    data = service.get_monthly_trend(months=months)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def pareto_analysis(request):
    """
    Get Pareto analysis
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(request.user.profile.organization)
    data = service.get_pareto_analysis()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def tail_spend_analysis(request):
    """
    Get tail spend analysis
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    threshold = validate_int_param(request, 'threshold', 20, min_val=1, max_val=100)
    service = AnalyticsService(request.user.profile.organization)
    data = service.get_tail_spend_analysis(threshold_percentage=threshold)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def spend_stratification(request):
    """
    Get spend stratification (Kraljic Matrix)
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(request.user.profile.organization)
    data = service.get_spend_stratification()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def seasonality_analysis(request):
    """
    Get seasonality analysis
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(request.user.profile.organization)
    data = service.get_seasonality_analysis()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def year_over_year(request):
    """
    Get year over year comparison
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(request.user.profile.organization)
    data = service.get_year_over_year_comparison()

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([ReadAPIThrottle])
def consolidation_opportunities(request):
    """
    Get supplier consolidation opportunities
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = AnalyticsService(request.user.profile.organization)
    data = service.get_supplier_consolidation_opportunities()

    return Response(data)


# ============================================================================
# AI Insights Endpoints
# ============================================================================

def _get_ai_service(request):
    """
    Helper to create AI Insights Service with user preferences.
    """
    profile = request.user.profile
    ai_settings = getattr(profile, 'ai_settings', {}) or {}

    return AIInsightsService(
        organization=profile.organization,
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = _get_ai_service(request)
    data = service.get_all_insights()

    log_action(
        user=request.user,
        action='view',
        resource='ai_insights',
        request=request,
        details={'insight_count': data['summary']['total_insights']}
    )

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([AIInsightsThrottle])
def ai_insights_cost(request):
    """
    Get cost optimization insights only.

    Identifies price variance across suppliers and potential savings.
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = _get_ai_service(request)
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = _get_ai_service(request)
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    # Parse sensitivity parameter
    try:
        sensitivity = float(request.query_params.get('sensitivity', 2.0))
        sensitivity = max(1.0, min(5.0, sensitivity))  # Clamp to range
    except (ValueError, TypeError):
        sensitivity = 2.0

    service = _get_ai_service(request)
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    months = validate_int_param(request, 'months', 6, min_val=1, max_val=24)

    service = PredictiveAnalyticsService(request.user.profile.organization)
    data = service.get_spending_forecast(months=months)

    log_action(
        user=request.user,
        action='view',
        resource='spending_forecast',
        request=request,
        details={'months': months}
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    months = validate_int_param(request, 'months', 6, min_val=1, max_val=24)

    service = PredictiveAnalyticsService(request.user.profile.organization)
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    months = validate_int_param(request, 'months', 6, min_val=1, max_val=24)

    service = PredictiveAnalyticsService(request.user.profile.organization)
    data = service.get_supplier_forecast(supplier_id=supplier_id, months=months)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([PredictionsThrottle])
def trend_analysis(request):
    """
    Get comprehensive trend analysis across all dimensions.
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = PredictiveAnalyticsService(request.user.profile.organization)
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
    """
    if not hasattr(request.user, 'profile'):
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

    service = PredictiveAnalyticsService(request.user.profile.organization)
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = ContractAnalyticsService(request.user.profile.organization)
    data = service.get_contract_overview()

    log_action(
        user=request.user,
        action='view',
        resource='contract_overview',
        request=request
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = ContractAnalyticsService(request.user.profile.organization)
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = ContractAnalyticsService(request.user.profile.organization)
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    days = validate_int_param(request, 'days', 90, min_val=1, max_val=365)

    service = ContractAnalyticsService(request.user.profile.organization)
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = ContractAnalyticsService(request.user.profile.organization)
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = ContractAnalyticsService(request.user.profile.organization)
    data = service.get_savings_opportunities()

    log_action(
        user=request.user,
        action='view',
        resource='contract_savings',
        request=request
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = ContractAnalyticsService(request.user.profile.organization)
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

    Returns:
    - Contract value vs actual spend
    - Variance analysis
    - Monthly comparison trend
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    contract_id = request.query_params.get('contract_id')
    if contract_id:
        try:
            contract_id = int(contract_id)
        except (ValueError, TypeError):
            return Response({'error': 'contract_id must be an integer'}, status=400)

    service = ContractAnalyticsService(request.user.profile.organization)
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = ComplianceService(request.user.profile.organization)
    data = service.get_compliance_overview()

    log_action(
        user=request.user,
        action='view',
        resource='compliance_overview',
        request=request
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = ComplianceService(request.user.profile.organization)
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
    """
    if not hasattr(request.user, 'profile'):
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

    service = ComplianceService(request.user.profile.organization)
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    months = validate_int_param(request, 'months', 12, min_val=1, max_val=36)

    service = ComplianceService(request.user.profile.organization)
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    resolution_notes = request.data.get('resolution_notes', '')
    if not resolution_notes:
        return Response({'error': 'resolution_notes is required'}, status=400)

    service = ComplianceService(request.user.profile.organization)
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
        details={'resolution_notes': resolution_notes}
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = ComplianceService(request.user.profile.organization)
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
    """
    if not hasattr(request.user, 'profile'):
        return Response({'error': 'User profile not found'}, status=400)

    service = ComplianceService(request.user.profile.organization)
    data = service.get_policies_list()

    return Response({
        'policies': data,
        'count': len(data)
    })
