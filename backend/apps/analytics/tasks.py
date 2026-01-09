"""
Celery tasks for analytics module.

Contains background tasks for:
- Refreshing materialized views after data uploads
- Pre-computing analytics for large datasets
- Async AI enhancement processing
- Deep insight analysis
"""
import logging
import json
from celery import shared_task
from django.db import connection
from django.core.cache import cache

logger = logging.getLogger(__name__)


@shared_task(
    name='refresh_materialized_views',
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
    track_started=True,
)
def refresh_materialized_views(self):
    """
    Refresh all analytics materialized views concurrently.

    This task should be triggered after data uploads complete.
    Uses CONCURRENTLY option to avoid locking the views during refresh.

    Returns:
        dict: Status and count of views refreshed
    """
    views = [
        'mv_monthly_category_spend',
        'mv_monthly_supplier_spend',
        'mv_daily_transaction_summary',
    ]

    refreshed = 0
    errors = []

    with connection.cursor() as cursor:
        for view in views:
            try:
                # Use CONCURRENTLY to avoid locking (requires unique index)
                cursor.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}")
                refreshed += 1
                logger.info(f"Refreshed materialized view: {view}")
            except Exception as e:
                error_msg = f"Failed to refresh {view}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

                # Try non-concurrent refresh as fallback
                try:
                    cursor.execute(f"REFRESH MATERIALIZED VIEW {view}")
                    refreshed += 1
                    logger.info(f"Refreshed materialized view (non-concurrent): {view}")
                    errors.pop()  # Remove error if fallback succeeded
                except Exception as e2:
                    logger.error(f"Fallback refresh also failed for {view}: {str(e2)}")

    return {
        'status': 'success' if not errors else 'partial',
        'views_refreshed': refreshed,
        'total_views': len(views),
        'errors': errors,
    }


@shared_task(
    name='refresh_single_materialized_view',
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def refresh_single_view(self, view_name: str):
    """
    Refresh a single materialized view.

    Args:
        view_name: Name of the materialized view to refresh

    Returns:
        dict: Status of the refresh operation
    """
    valid_views = {
        'mv_monthly_category_spend',
        'mv_monthly_supplier_spend',
        'mv_daily_transaction_summary',
    }

    if view_name not in valid_views:
        return {
            'status': 'error',
            'message': f"Invalid view name: {view_name}. Valid views: {valid_views}"
        }

    with connection.cursor() as cursor:
        try:
            cursor.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}")
            logger.info(f"Refreshed materialized view: {view_name}")
            return {
                'status': 'success',
                'view': view_name,
            }
        except Exception as e:
            logger.error(f"Failed to refresh {view_name}: {str(e)}")
            # Try non-concurrent as fallback
            try:
                cursor.execute(f"REFRESH MATERIALIZED VIEW {view_name}")
                return {
                    'status': 'success',
                    'view': view_name,
                    'note': 'Used non-concurrent refresh',
                }
            except Exception as e2:
                return {
                    'status': 'error',
                    'view': view_name,
                    'message': str(e2),
                }


# ============================================================================
# Async AI Enhancement Tasks
# ============================================================================

ENHANCEMENT_STATUS_PREFIX = "ai_enhancement_status"
ENHANCEMENT_RESULT_PREFIX = "ai_enhancement_result"
ENHANCEMENT_CACHE_TTL = 300  # 5 minutes


@shared_task(
    name='enhance_insights_async',
    bind=True,
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    track_started=True,
)
def enhance_insights_async(self, org_id: int, user_id: int, insights_data: list):
    """
    Async task to enhance insights with external AI.

    Results are stored in cache for polling by frontend.

    Args:
        org_id: Organization ID
        user_id: User ID who requested the enhancement
        insights_data: List of insight dictionaries to enhance

    Returns:
        dict: Status and result of the enhancement
    """
    from apps.authentication.models import Organization, UserProfile
    from .ai_services import AIInsightsService

    status_key = f"{ENHANCEMENT_STATUS_PREFIX}:{org_id}:{user_id}"
    result_key = f"{ENHANCEMENT_RESULT_PREFIX}:{org_id}:{user_id}"

    try:
        cache.set(status_key, {"status": "processing", "progress": 10}, ENHANCEMENT_CACHE_TTL)

        org = Organization.objects.get(id=org_id)
        profile = UserProfile.objects.filter(user_id=user_id).first()

        if not profile:
            cache.set(status_key, {"status": "failed", "error": "User profile not found"}, ENHANCEMENT_CACHE_TTL)
            return {"status": "failed", "error": "User profile not found"}

        ai_settings = getattr(profile, 'ai_settings', None) or profile.preferences.get('ai_settings', {})

        cache.set(status_key, {"status": "processing", "progress": 30}, ENHANCEMENT_CACHE_TTL)

        service = AIInsightsService(
            organization=org,
            use_external_ai=True,
            ai_provider=ai_settings.get('ai_provider', 'anthropic'),
            api_key=ai_settings.get('ai_api_key')
        )

        cache.set(status_key, {"status": "processing", "progress": 50}, ENHANCEMENT_CACHE_TTL)

        enhancement = service._enhance_with_external_ai_structured(insights_data)

        if enhancement:
            cache.set(status_key, {"status": "processing", "progress": 90}, ENHANCEMENT_CACHE_TTL)
            cache.set(result_key, enhancement, ENHANCEMENT_CACHE_TTL)
            cache.set(status_key, {"status": "completed", "progress": 100}, ENHANCEMENT_CACHE_TTL)

            logger.info(f"AI enhancement completed for org {org_id}")
            return {"status": "completed", "org_id": org_id}
        else:
            cache.set(status_key, {
                "status": "failed",
                "error": "AI enhancement returned no results",
                "progress": 0
            }, ENHANCEMENT_CACHE_TTL)
            return {"status": "failed", "error": "No enhancement results"}

    except Organization.DoesNotExist:
        error_msg = f"Organization {org_id} not found"
        logger.error(error_msg)
        cache.set(status_key, {"status": "failed", "error": error_msg, "progress": 0}, ENHANCEMENT_CACHE_TTL)
        return {"status": "failed", "error": error_msg}

    except Exception as e:
        error_msg = f"AI enhancement failed: {str(e)}"
        logger.error(f"AI enhancement failed for org {org_id}: {e}")
        cache.set(status_key, {"status": "failed", "error": error_msg, "progress": 0}, ENHANCEMENT_CACHE_TTL)
        raise


@shared_task(
    name='perform_deep_analysis_async',
    bind=True,
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    track_started=True,
)
def perform_deep_analysis_async(self, org_id: int, user_id: int, insight_data: dict):
    """
    Async task to perform deep analysis on a specific insight.

    Args:
        org_id: Organization ID
        user_id: User ID who requested the analysis
        insight_data: The insight to analyze deeply

    Returns:
        dict: Deep analysis results
    """
    from apps.authentication.models import Organization, UserProfile
    from .ai_services import AIInsightsService

    insight_id = insight_data.get('id', 'unknown')
    status_key = f"deep_analysis_status:{org_id}:{insight_id}"
    result_key = f"deep_analysis_result:{org_id}:{insight_id}"

    try:
        cache.set(status_key, {"status": "processing", "progress": 10}, ENHANCEMENT_CACHE_TTL)

        org = Organization.objects.get(id=org_id)
        profile = UserProfile.objects.filter(user_id=user_id).first()

        if not profile:
            cache.set(status_key, {"status": "failed", "error": "User profile not found"}, ENHANCEMENT_CACHE_TTL)
            return {"status": "failed", "error": "User profile not found"}

        ai_settings = getattr(profile, 'ai_settings', None) or profile.preferences.get('ai_settings', {})

        cache.set(status_key, {"status": "processing", "progress": 30}, ENHANCEMENT_CACHE_TTL)

        service = AIInsightsService(
            organization=org,
            use_external_ai=True,
            ai_provider=ai_settings.get('ai_provider', 'anthropic'),
            api_key=ai_settings.get('ai_api_key')
        )

        cache.set(status_key, {"status": "processing", "progress": 50}, ENHANCEMENT_CACHE_TTL)

        analysis = service.perform_deep_analysis(insight_data)

        if analysis:
            cache.set(status_key, {"status": "processing", "progress": 90}, ENHANCEMENT_CACHE_TTL)
            cache.set(result_key, analysis, ENHANCEMENT_CACHE_TTL)
            cache.set(status_key, {"status": "completed", "progress": 100}, ENHANCEMENT_CACHE_TTL)

            logger.info(f"Deep analysis completed for insight {insight_id} in org {org_id}")
            return {"status": "completed", "insight_id": insight_id}
        else:
            cache.set(status_key, {
                "status": "failed",
                "error": "Deep analysis returned no results",
                "progress": 0
            }, ENHANCEMENT_CACHE_TTL)
            return {"status": "failed", "error": "No analysis results"}

    except Organization.DoesNotExist:
        error_msg = f"Organization {org_id} not found"
        logger.error(error_msg)
        cache.set(status_key, {"status": "failed", "error": error_msg, "progress": 0}, ENHANCEMENT_CACHE_TTL)
        return {"status": "failed", "error": error_msg}

    except Exception as e:
        error_msg = f"Deep analysis failed: {str(e)}"
        logger.error(f"Deep analysis failed for insight {insight_id} in org {org_id}: {e}")
        cache.set(status_key, {"status": "failed", "error": error_msg, "progress": 0}, ENHANCEMENT_CACHE_TTL)
        raise
