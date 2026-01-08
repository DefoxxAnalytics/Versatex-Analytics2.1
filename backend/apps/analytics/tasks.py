"""
Celery tasks for analytics module.

Contains background tasks for:
- Refreshing materialized views after data uploads
- Pre-computing analytics for large datasets
"""
import logging
from celery import shared_task
from django.db import connection

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
