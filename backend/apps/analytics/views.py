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
