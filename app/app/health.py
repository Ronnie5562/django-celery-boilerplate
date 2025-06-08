from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache


def health_check(request):
    """
    Simple health check endpoint
    """
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Test cache
        cache.set('health_check', 'ok', 10)
        cache_status = cache.get('health_check')

        return JsonResponse({
            'status': 'healthy',
            'database': 'ok',
            'cache': 'ok' if cache_status == 'ok' else 'error'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)
